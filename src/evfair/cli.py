import argparse,json
from pathlib import Path

def worker(seed,protocol,out):
    from .experiment import evaluate
    evaluate(protocol,out,[seed])

def main():
    p=argparse.ArgumentParser(description='Reproducible EV charging audit and experiments')
    p.add_argument('stage',choices=['validate-data','validate','evaluate','report','supplement'])
    p.add_argument('--protocol',default='config/protocol.json');p.add_argument('--out',default='results')
    p.add_argument('--input',default='data/raw/ornl_acn.json');p.add_argument('--workers',type=int,default=1)
    args=p.parse_args();protocol=json.loads(Path(args.protocol).read_text())
    if args.stage=='validate-data':
        from .data import normalize,save_sessions
        from .experiment import dumps,digest
        from collections import Counter
        s,a,r=normalize(args.input)
        a['repeat_count_distribution']={str(k):v for k,v in Counter(Counter(x.user for x in s).values()).items()}
        a['source_sha256']=digest(args.input)
        dumps(Path(args.out)/'data_audit.json',a);dumps(Path(args.out)/'data_exclusions.json',r)
        save_sessions(s,'data/processed/ornl_sessions.json');print(json.dumps(a,indent=2))
    elif args.stage=='validate':
        from .experiment import validate
        validate(protocol,args.out)
    elif args.stage=='evaluate':
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            jobs=[pool.submit(worker,seed,protocol,args.out) for seed in protocol['seeds']]
            for j in jobs:j.result()
    elif args.stage=='supplement':
        from .supplement import run
        run(protocol,args.out,args.workers)
    elif args.stage=='report':
        from .report import report
        report(protocol,args.out)

if __name__=='__main__':main()
