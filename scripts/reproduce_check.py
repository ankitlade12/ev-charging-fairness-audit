"""Fresh-environment reproduction of training and the primary paired replay."""
from pathlib import Path
import json,platform,time
import numpy as np
import pandas as pd
from evfair.experiment import prepare,run_one,dumps

if __name__=='__main__':
    protocol=json.load(open('config/protocol.json'));lock=json.load(open('results/protocol_lock.json'))
    out=Path('results/reproduction');t=time.perf_counter()
    parts,model,peak=prepare(11,protocol,out)
    checks={}
    for name in ['history',lock['comparator']]:
        score=run_one(parts['test'],model,name,peak*.35,lock['selected'][name],out/name,trace=True)
        reference=Path('results/seed_11/cap_0.35')/name/'sessions.csv'
        while not reference.exists():
            time.sleep(2)  # Separate background verification process only.
        actual=pd.read_csv(out/name/'sessions.csv').sort_values('sid').reset_index(drop=True)
        expected=pd.read_csv(reference).sort_values('sid').reset_index(drop=True)
        assert actual.sid.equals(expected.sid)
        differences={k:float(np.max(np.abs(actual[k]-expected[k]))) for k in ['requested','delivered','shortfall','cost']}
        assert max(differences.values())<1e-7,differences
        checks[name]=differences
    dumps(out/'verification.json',dict(python=platform.python_version(),tolerance=1e-7,passed=True,checks=checks,elapsed_seconds=time.perf_counter()-t,
         limitation='Separate clean Python environment, same machine and agent; not independent human reproduction.'))
    print(checks)
