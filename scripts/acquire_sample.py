"""Download only the public 26-record ORNL discovery sample; never an ACN API token."""
from pathlib import Path
import json,hashlib,datetime
import requests

base='https://openenergyhub.ornl.gov/api/explore/v2.1/catalog/datasets/acn-data'
out=Path('data/raw');out.mkdir(parents=True,exist_ok=True)
manifest=[]
for name,url in [('ornl_metadata.json',base),('ornl_records.json',base+'/records?limit=100')]:
    r=requests.get(url,timeout=30);r.raise_for_status();obj=r.json()
    if name=='ornl_records.json':
        if len(obj['results'])!=obj['total_count']:raise ValueError('incomplete discovery sample; do not silently truncate')
    (out/name).write_bytes(r.content)
    manifest.append(dict(file=name,url=url,sha256=hashlib.sha256(r.content).hexdigest(),retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
items=[]
for x in json.loads((out/'ornl_records.json').read_text())['results']:
    names={'sessionid':'sessionID','userid':'userID','stationid':'stationID','siteid':'siteID','connectiontime':'connectionTime','disconnecttime':'disconnectTime','userinputs':'userInputs','timezone':'timezone','kwhdelivered':'kWhDelivered'}
    d={v:x[k] for k,v in names.items()};d['userInputs']=json.loads(d['userInputs']) if d['userInputs'] else []
    items.append(d)
(out/'ornl_acn.json').write_text(json.dumps({'_items':items},indent=2))
(out/'acquisition_manifest.json').write_text(json.dumps(manifest,indent=2))
print(f'Saved {len(items)} sample records. This is not the full ACN dataset.')
