"""Strict ACN normalization. Future timestamps remain evaluator-owned."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import Counter
from pathlib import Path
import hashlib, json, math
import pandas as pd

DT = 0.25
STEP = 900

@dataclass(frozen=True)
class Revision:
    at: int
    energy: float
    deadline: int | None

@dataclass(frozen=True)
class Session:
    sid: str
    user: str
    station: str
    site: str
    arrival: int
    departure: int
    revisions: tuple[Revision, ...]
    pmax: float = 6.6
    eta: float = 0.92
    def request_at(self, t):
        found = [r for r in self.revisions if r.at <= t]
        return found[-1] if found else None


def timestamp(x):
    if x is None: raise ValueError('missing timestamp')
    t = pd.Timestamp(x)
    if pd.isna(t) or t.tzinfo is None: raise ValueError('timestamp must have timezone')
    return t.timestamp()


def normalize(path, site='caltech'):
    """15-min conservative rounding; retain only positive active requests.

    Round arrivals/requests up and departures down. No future partial-slot
    availability is exposed. Exclude cross-local-day sessions for independent
    daily offline solves; record this selection explicitly.
    """
    blob = json.loads(Path(path).read_text())  # Truncated exports fail closed.
    items = blob['_items'] if isinstance(blob, dict) else blob
    if not isinstance(items, list) or not items: raise ValueError('empty or malformed dataset')
    audit = Counter(raw_sessions=len(items)); sessions=[]; seen=set(); reasons=[]
    for x in items:
        reason=None
        try:
            sid=str(x['sessionID'])
            if sid in seen: reason='duplicate_session'
            seen.add(sid)
            a=timestamp(x['connectionTime']); d=timestamp(x['disconnectTime'])
            if d <= a: reason=reason or 'nonpositive_duration'
            if not x.get('userID'): reason=reason or 'missing_identity'
            rev=[]
            for r in x.get('userInputs') or []:
                try:
                    at=timestamp(r['modifiedAt']); e=float(r['kWhRequested'])
                    if not math.isfinite(e) or e<=0: raise ValueError('invalid energy')
                    dep=timestamp(r['requestedDeparture']) if r.get('requestedDeparture') else None
                    if at<d:
                        rev.append(Revision(math.ceil(max(at,a)/STEP),e,math.ceil(dep/STEP) if dep else None))
                    else: audit['post_departure_revisions_ignored']+=1
                except (ValueError,KeyError,TypeError): audit['invalid_revisions_ignored']+=1
            rev.sort(key=lambda r:r.at)
            # Conflicting updates with indistinguishable availability cannot be ordered safely.
            if any(r.at==q.at and r!=q for r,q in zip(rev,rev[1:])): reason=reason or 'ambiguous_revision_bin'
            if not rev: reason=reason or 'missing_valid_request'
            aidx=math.ceil(a/STEP); didx=math.floor(d/STEP)
            if rev and rev[0].at>=didx: reason=reason or 'no_full_service_slot'
            if didx<=aidx: reason=reason or 'no_full_connection_slot'
            tz=x.get('timezone') or 'America/Los_Angeles'
            if pd.Timestamp(a,unit='s',tz='UTC').tz_convert(tz).date()!=pd.Timestamp(d,unit='s',tz='UTC').tz_convert(tz).date():
                reason=reason or 'cross_local_day'
            if d-a>24*3600: reason=reason or 'over_24h'
            if reason is None:
                user=hashlib.sha256((site+':'+str(x['userID'])).encode()).hexdigest()[:16]
                sessions.append(Session(sid,user,str(x.get('stationID',sid)),site,aidx,didx,tuple(rev)))
                audit['eligible_before_overlap']+=1
                audit['late_first_request']+=int(rev[0].at>aidx)
                audit['energy_revision_sessions']+=int(len({r.energy for r in rev})>1)
                audit['rounding_lost_hours']+=(aidx*STEP-a+d-didx*STEP)/3600
        except (ValueError,KeyError,TypeError,OverflowError): reason=reason or 'invalid_record'
        if reason: audit['excluded_'+reason]+=1; reasons.append({'sid':str(x.get('sessionID','unknown')),'reason':reason})
    # Exclude BOTH sessions in a same-station overlap. Otherwise cap validation is misleading.
    bad=set()
    for station in {s.station for s in sessions}:
        ss=sorted((s for s in sessions if s.station==station),key=lambda s:s.arrival)
        for i,s in enumerate(ss):
            for q in ss[i+1:]:
                if q.arrival>=s.departure: break
                bad.update([s.sid,q.sid])
    audit['excluded_station_overlap']=len(bad)
    sessions=[s for s in sessions if s.sid not in bad]
    audit['eligible_sessions']=len(sessions);audit['eligible_users']=len({s.user for s in sessions})
    return sorted(sessions,key=lambda s:(s.arrival,s.sid)),dict(audit),reasons


def save_sessions(sessions,path):
    Path(path).write_text(json.dumps([asdict(s) for s in sessions],indent=2))


def load_sessions(path):
    return [Session(**{**s,'revisions':tuple(Revision(**r) for r in s['revisions'])}) for s in json.loads(Path(path).read_text())]


def local_day(t):
    return pd.Timestamp(t*STEP,unit='s',tz='UTC').tz_convert('America/Los_Angeles').strftime('%Y-%m-%d')


def split_sessions(sessions,dates):
    out={k:[] for k in ['train','calibration','validation','test']}; excluded=0
    edges=[int(pd.Timestamp(d,tz='America/Los_Angeles').timestamp()/STEP) for d in dates]
    for s in sessions:
        assigned=False
        for k,l,r in zip(out,edges,edges[1:]):
            if s.arrival>=l and s.departure<r:out[k].append(s);assigned=True;break
        if not assigned:excluded+=1
    return out,excluded
