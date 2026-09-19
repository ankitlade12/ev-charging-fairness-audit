"""Versioned normalization sensitivity: preserve exact revision ordering before binning.
No primary source/output changes; only aggregate real-data summaries are saved.
"""
import json, math, tempfile
from copy import deepcopy
from collections import Counter, defaultdict
from pathlib import Path
from evfair.data import normalize, timestamp, STEP


def ordered_input(blob):
    records=blob['_items'] if isinstance(blob,dict) else blob
    counts=Counter(str(x.get('sessionID')) for x in records)
    out=[];audit=Counter(raw_sessions=len(records))
    for source in records:
        x=deepcopy(source)
        if counts[str(x.get('sessionID'))]>1:
            audit['all_duplicate_id_records_quarantined']+=1
            continue
        try:
            a=timestamp(x['connectionTime']);d=timestamp(x['disconnectTime'])
            bins=defaultdict(list);invalid=False
            for r in x.get('userInputs') or []:
                at=timestamp(r['modifiedAt']);energy=float(r['kWhRequested'])
                if not math.isfinite(energy) or energy<=0:invalid=True;break
                dep=timestamp(r['requestedDeparture']) if r.get('requestedDeparture') else None
                if at<d:bins[math.ceil(max(at,a)/STEP)].append((at,energy,dep,r))
            if invalid:
                audit['invalid_revision_record_quarantined']+=1;continue
            revised=[];ambiguous=False
            for entries in bins.values():
                same_time=defaultdict(set)
                for at,energy,dep,r in entries:same_time[at].add((energy,dep))
                if any(len(values)>1 for values in same_time.values()):ambiguous=True;break
                # Every update in this bin is already available at its decision boundary.
                chosen=max(entries,key=lambda v:v[0]);revised.append(chosen[3])
                audit['superseded_same_bin_updates']+=len(entries)-1
            if ambiguous:
                audit['conflicting_exact_timestamp_record_quarantined']+=1;continue
            x['userInputs']=revised;out.append(x)
        except (KeyError,ValueError,TypeError,OverflowError):
            audit['invalid_record_quarantined']+=1
    return {'_items':out},dict(audit)

if __name__=='__main__':
    path=Path('data/raw/ornl_acn.json')
    adjusted,pre=ordered_input(json.loads(path.read_text()))
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'ordered.json';p.write_text(json.dumps(adjusted))
        ss,audit,_=normalize(p)
    user_counts=Counter(s.user for s in ss)
    result=dict(status='post-primary data adapter sensitivity; original 12-session audit retained',preprocessing=pre,normalization=audit,eligible_sessions=len(ss),eligible_users=len(user_counts),users_with_at_least_five_sessions=sum(v>=5 for v in user_counts.values()),repeat_count_histogram=dict(Counter(user_counts.values())),scope='No request values, identities or raw records exported; not an empirical fairness evaluation.')
    Path('results/second_pass/revision_order_audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
