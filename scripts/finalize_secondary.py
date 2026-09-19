"""Additional reporting; no fitting or retuning from test scores."""
from pathlib import Path
import json
import pandas as pd
from evfair.metrics import paired_seed_interval
from evfair.experiment import dumps

p=Path('results/tables');scores=pd.read_csv('results/test_scores.csv');primary=scores[scores.capacity_fraction==.35]
a=primary[primary.policy=='history'].set_index('seed');b=primary[primary.policy=='pf_mpc'].set_index('seed')
rows=[]
for metric in ['tail','delivered','cost_per_kwh','new_shortfall']:
    v=(a[metric]/b[metric] if metric in ['delivered','cost_per_kwh'] else a[metric]-b[metric]).drop(index=11)
    rows.append(dict(metric=metric,**paired_seed_interval(v)))
pd.DataFrame(rows).to_csv(p/'excluding_development_population.csv',index=False)
fs=pd.read_csv(p/'forecast_scores.csv');means=fs.groupby(['model','lead_minutes'])[['brier','logloss']].mean()
sub=pd.read_csv(p/'supplement_effects.csv');text=[]
f=means.loc[('empirical',60),'brier'];h=means.loc[('hazard',60),'brier'];c=means.loc[('hazard_cal',60),'brier']
text.append(f'At the original one-hour landmark and 60-minute lead, mean Brier scores are {f:.4f} for empirical durations, {h:.4f} for the uncalibrated hazard and {c:.4f} after calibration. These forecast scores alone do not establish better control.')
for variant in ['uncalibrated','empirical','early','late','wide','narrow']:
    r=sub[(sub.variant==variant)&(sub.policy=='history')&(sub.metric=='tail')].iloc[0]
    label={'uncalibrated':'Removing calibration','empirical':'Substituting empirical durations','early':'Earlier forecasts','late':'Later forecasts','wide':'Wider forecasts','narrow':'Narrower forecasts'}[variant]
    if variant in ['uncalibrated','late']:
        text.append(f"{label} {'changes' if variant=='uncalibrated' else 'change'} candidate tail shortfall by {100*r['mean']:.2f} percentage points (interval [{100*r.low:.2f},{100*r.high:.2f}]) relative to its unperturbed run.")
stress=pd.read_csv('results/supplement_scores.csv')
for variant in ['shorter_stay','larger_requests']:
    aa=stress[(stress.variant==variant)&(stress.policy=='history')].set_index('seed')
    bb=stress[(stress.variant==variant)&(stress.policy=='pf_mpc')].set_index('seed')
    r=paired_seed_interval(aa['tail']-bb['tail'])
    text.append(f"Under {'shorter stays' if variant=='shorter_stay' else 'larger requests'}, the candidate-minus-comparator tail change is {100*r['mean']:.2f} percentage points ([{100*r['low']:.2f},{100*r['high']:.2f}]).")
row=rows[0]
text.append(f"Because seed 11 also supplies controller validation, a sensitivity excludes that development population. Across the remaining four populations, tail change is {100*row['mean']:.2f} percentage points ([{100*row['low']:.2f},{100*row['high']:.2f}]). This guards against mistaking within-population temporal validation for wholly independent population selection.")
Path('manuscript/secondary_results.tex').write_text('\n\n'.join(text)+'\n')
with open('docs/results_report.md','a') as f:f.write('\n## Additional interpretation and development-population sensitivity\n\n'+'\n\n'.join(text)+'\n')
print('\n'.join(text))
