"""Generate second-pass manuscript content and figure from saved diagnostics."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import t
P=Path('results/second_pass')
scores=pd.read_csv(P/'lexicographic_scores.csv');pairs=pd.read_csv(P/'lexicographic_paired_intervals.csv')
f=pd.read_csv(P/'forecast_by_landmark.csv');overall=pd.read_csv(P/'forecast_session_balanced.csv');fi=pd.read_csv(P/'forecast_paired_intervals.csv')

def interval(a,b):
    r=pairs[(pairs.candidate==a)&(pairs.comparator==b)&(pairs.metric=='tail')].iloc[0]
    return f"{r['mean']:.2f} percentage points (95\\% interval [{r.low:.2f},{r.high:.2f}])"

text=r'''\subsection{Second-pass numerical and forecast audit}
After inspecting primary outcomes, we applied the same two-stage tie-breaking diagnostic to all five MPC variants, retaining their original settings. The first LP minimizes the original objective; the second minimizes slot-index-weighted planned energy within $10^{-7}$ dollars of that optimum. A secondary solution is accepted within $2\times10^{-7}$ dollars; otherwise the first is used. Existing action checks and fallback remain active. These 25 runs reuse inspected populations and are exploratory, not a replacement confirmatory experiment.

'''
means=scores.groupby('policy')['tail'].mean()*100
text+=f"Point MPC's mean tail shortfall becomes {means['point']:.2f}\\%, compared with 29.75\\% in the original implementation. The uncertainty-only minus point contrast is {interval('stochastic','point')}; full-history minus point-history is {interval('history','point_history')}. Thus an incremental control benefit from distribution information is not established by these comparisons. History minus proportional-fair MPC remains {interval('history','pf_mpc')}. The diagnostic has {int(scores.fallbacks.sum())} applied fallback decisions, all satisfying the original action tolerance.\n\n"
text+=r'''The original one-hour landmark has only 18 departure events at the 60-minute lead. We therefore added fixed landmarks at 1, 3, 5, 7 and 9 hours and leads of 30, 60, 120 and 240 minutes, without refitting or selecting a forecast. Scores first average over available landmarks within each session, then over sessions within each population. This gives equal total weight to sessions rather than to repeated predictions. It evaluates surviving connected sessions, not only sessions with remaining demand.

'''
g=overall[overall.lead_minutes==60].groupby('model').brier.mean();r=fi[(fi.lead_minutes==60)&(fi.metric=='brier')&(fi.comparator=='empirical')].iloc[0]
text+=f"At a 60-minute lead, session-balanced Brier scores are {g['empirical']:.4f} for empirical durations and {g['hazard_cal']:.4f} for calibrated hazards; their paired change is {r['mean']:.4f} ([{r.low:.4f},{r.high:.4f}]). Calibration versus the uncalibrated hazard has an inconclusive contrast. Figure~\\ref{{fig:calibration}} shows why the original early landmark was uninformative. Improved prediction scores do not by themselves establish better service allocation.\n"
Path('manuscript/second_pass_results.tex').write_text(text)
plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'ps.fonttype':42})
fig,axes=plt.subplots(2,1,figsize=(3.45,3.25),sharex=True,gridspec_kw={'height_ratios':[2,1]})
for name,label in [('empirical','Empirical'),('hazard','Hazard'),('hazard_cal','Calibrated hazard')]:
    x=f[(f.model==name)&(f.lead_minutes==60)].groupby('landmark_hours').brier
    a=x.mean();half=t.ppf(.975,4)*x.std()/np.sqrt(5)
    axes[0].errorbar(a.index,a.values,yerr=half.values,marker='o',ms=3,capsize=2,label=label)
axes[0].set_ylabel('Brier score');axes[0].legend(fontsize=7,loc='upper left');axes[0].grid(alpha=.2)
counts=f[(f.model=='hazard_cal')&(f.lead_minutes==60)].groupby('landmark_hours')[['n','events']].sum()
axes[1].bar(counts.index,counts.events/counts.n,width=.65,color='#496b7c')
for age,row in counts.iterrows():axes[1].text(age,row.events/row.n+.025,f'{int(row.events)}/{int(row.n)}',ha='center',fontsize=6.5)
axes[1].set_ylim(0,.8);axes[1].set_ylabel('Event rate');axes[1].set_xlabel('Hours after request activation');axes[1].set_xticks(counts.index)
fig.tight_layout(pad=.3);fig.savefig('figures/forecast_landmarks.pdf');plt.close(fig)
summary=scores.groupby('policy')[['tail','delivered','cost_per_kwh','fallbacks']].agg({'tail':'mean','delivered':'mean','cost_per_kwh':'mean','fallbacks':'sum'})
summary.to_csv(P/'lexicographic_means.csv')
print(summary)
# Capacity view includes the simple history-sharing baseline.
primary=pd.read_csv('results/test_scores.csv')
fig,axes=plt.subplots(1,2,figsize=(7.0,2.8))
styles=[('equal','Equal sharing','#999999'),('maxmin','Max-min fulfillment','#5f8c6f'),('debt_share','History sharing','#d23f8d'),('point','Point MPC (original)','#7954a1'),('stochastic','Uncertainty only','#c57a13'),('pf_mpc','Proportional-fair MPC','#333333'),('history','History + uncertainty','#1264a2')]
for name,label,color in styles:
    a=primary[primary.policy==name].groupby('capacity_fraction')[['tail','delivered']].mean()
    axes[0].plot(a.index,100*a['tail'],marker='o',ms=3,label=label,color=color)
    axes[1].plot(a.index,a.delivered/1000,marker='o',ms=3,color=color)
axes[0].set_ylabel('Worst-decile shortfall (%)');axes[1].set_ylabel('Delivered energy (MWh)')
for ax in axes:ax.set_xlabel('Capacity / training peak');ax.spines[['top','right']].set_visible(False)
axes[0].legend(fontsize=6.5,loc='upper right');fig.tight_layout(pad=.4)
fig.savefig('figures/capacity_audit.pdf');fig.savefig('figures/capacity_audit.png',dpi=200);plt.close(fig)
