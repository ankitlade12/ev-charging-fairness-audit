from pathlib import Path
import pandas as pd
from evfair.metrics import paired_seed_interval
from evfair.experiment import dumps

p=Path('results/tables');s=pd.read_csv('results/test_scores.csv');s=s[s.capacity_fraction==.35]
a=s[s.policy=='history'].set_index('seed');b=s[s.policy=='debt_share'].set_index('seed')
rows=[]
for metric in ['tail','delivered','cost_per_kwh']:
    v=a[metric]-b[metric] if metric=='tail' else a[metric]/b[metric]
    rows.append(dict(metric=metric,**paired_seed_interval(v)))
pd.DataFrame(rows).to_csv(p/'history_vs_simple_sharing.csv',index=False)
frozen=pd.read_csv(p/'point_frozen_diagnostic.csv');lex=pd.read_csv(p/'point_lexicographic_diagnostic.csv')
point=s[s.policy=='point']
text=f'''The simpler history-weighted sharing policy has mean worst-tail shortfall {100*b['tail'].mean():.2f}%, compared with {100*a['tail'].mean():.2f}% for the full candidate. Candidate-minus-sharing difference is {100*rows[0]['mean']:.2f} percentage points (95% interval [{100*rows[0]['low']:.2f}, {100*rows[0]['high']:.2f}]); the interval does not establish a tail advantage for either. Candidate delivery is {100*rows[1]['mean']:.2f}% and its unit cost {100*rows[2]['mean']:.2f}% of simple sharing. This comparison does not replace the locked proportional-fair primary comparator. It limits any claim that the more complex controller is necessary.

A post-primary point-MPC diagnostic freezes the predicted deadline at arrival. Its mean tail shortfall is {100*frozen['tail'].mean():.2f}%, versus {100*point['tail'].mean():.2f}% for the original rolling-median point MPC. A second diagnostic minimizes planned energy-weighted slot index after constraining the economic objective within 1e-7 dollars of its first optimum. That lexicographic tie-break gives {100*lex['tail'].mean():.2f}% mean tail shortfall. This large change shows that point-MPC comparisons depend on optimization tie-breaking, not only departure uncertainty. The original 1e-9 preference is too small to reliably resolve numerical ties. Neither diagnostic is validation-selected or used to rewrite the locked primary result. The lexicographic diagnostic recorded {int(lex.fallbacks.sum())} feasible fallback decisions, included in its outcomes; it still obeys the applied-action tolerance. The full candidate's matched point comparison should therefore not be interpreted as an isolated causal estimate of the value of uncertainty.
'''
path=Path('docs/results_report.md');content=path.read_text();header='\n## Simpler-controller and numerical-tie diagnostics\n\n';content=content.split(header)[0];path.write_text(content+header+text)
print(text)
