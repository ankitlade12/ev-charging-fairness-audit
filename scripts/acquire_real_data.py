"""Acquire official ACN JPL records in small windows; never accept truncated JSON.
Raw records stay in ignored data/raw. Aggregate provenance is public.
"""
from pathlib import Path
import argparse, concurrent.futures, datetime as dt, hashlib, json, time
import requests
from bs4 import BeautifulSoup

RAW=Path('data/raw/real_study/jpl_windows')
OUT=Path('results/real_data')

def acquire_window(pair):
    start,end=pair;name=start.isoformat();p=RAW/(name+'.json');manifest=RAW/(name+'_manifest.json')
    if p.exists() and manifest.exists():
        m=json.loads(manifest.read_text())
        if m.get('complete') and m.get('end')==end.isoformat() and hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']:return m
    record={'start':name,'end':end.isoformat(),'site':'jpl','url':'https://ev.caltech.edu/dataset','retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat()}
    for attempt in range(2):
        try:
            session=requests.Session();page=session.get(record['url'],timeout=30);page.raise_for_status()
            token=BeautifulSoup(page.text,'html.parser').find('input',{'name':'csrf_token'})['value']
            form={'csrf_token':token,'site':'JPL','start':start.strftime('%m/%d/%Y 12:00 AM'),'end':end.strftime('%m/%d/%Y 12:00 AM'),'min_kWh':'0','submit':'Download'}
            count=session.post('https://ev.caltech.edu/_num_sessions',data=form,timeout=40);count.raise_for_status();expected=int(count.json()['result'])
            response=session.post(record['url'],data=form,timeout=65);response.raise_for_status();data=response.content
            blob=json.loads(data);assert blob['_meta']['site']=='jpl';items=blob['_items'];assert len(items)==expected,(len(items),expected)
            p.write_bytes(data);record.update(expected=expected,records=len(items),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),complete=True)
            record.pop('error',None);break
        except Exception as e:record.update(complete=False,error=str(e))
    manifest.write_text(json.dumps(record,indent=2));print(name,record.get('records'),record['complete'],record.get('error',''),flush=True)
    return record

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=3);args=parser.parse_args()
    RAW.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    start=dt.date(2019,1,1);stop=dt.date(2020,1,2);windows=[]
    while start<stop:
        end=min(start+dt.timedelta(days=7),stop);windows.append((start,end));start=end
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:records=list(pool.map(acquire_window,windows))
    failures=[r for r in records if not r['complete']]
    if failures:raise RuntimeError(f'{len(failures)} incomplete windows; no merged dataset produced')
    unique={};duplicates=0
    for record in records:
        for item in json.loads((RAW/(record['start']+'.json')).read_text())['_items']:
            sid=item['sessionID']
            if sid in unique:
                assert unique[sid]==item,'Conflicting duplicate session at window boundary';duplicates+=1
            unique[sid]=item
    path=RAW.parent/'jpl_2019_complete.json';path.write_text(json.dumps({'_items':list(unique.values())}))
    result={'source':'Caltech ACN-Data official public web export','year':2019,'site':'jpl','url':'https://ev.caltech.edu/dataset','windows':records,'raw_records':len(unique),'exact_duplicates_removed':duplicates,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'raw_path':str(path),'license_note':'Official dataset citation requested; raw records not redistributed. No standalone license inferred.'}
    (OUT/'acquisition.json').write_text(json.dumps(result,indent=2));print('COMPLETE',len(unique),flush=True)
if __name__=='__main__':main()
