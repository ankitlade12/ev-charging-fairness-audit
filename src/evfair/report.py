from pathlib import Path
import json,os,math,platform,hashlib
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/evfair-mpl')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .metrics import metrics,paired_seed_interval,paired_block_interval
from .experiment import dumps,digest

LABELS={'history':'History + uncertainty','pf_mpc':'Proportional-fair MPC','stochastic':'Uncertainty only','point_history':'Point + history','point':'Point MPC','equal':'Equal power','maxmin':'Max-min fulfillment','debt_share':'History-weighted sharing','fcfs':'FCFS','edf':'Declared EDF','laxity':'Least laxity'}
ORDER=['equal','fcfs','edf','laxity','maxmin','debt_share','point','stochastic','point_history','pf_mpc','history']

def table_md(df):
    rows=['| '+' | '.join(map(str,df.columns))+' |','| '+' | '.join(['---']*len(df.columns))+' |']
    for row in df.itertuples(index=False):rows.append('| '+' | '.join(str(x) for x in row)+' |')
    return '\n'.join(rows)

def report(protocol,out='results'):
    out=Path(out);figdir=Path('figures');figdir.mkdir(exist_ok=True);tables=out/'tables';tables.mkdir(exist_ok=True)
    lock=json.load(open(out/'protocol_lock.json'));comparator=lock['comparator'];rows=[];frames=[];oracles=[]
    for seed in protocol['seeds']:
        for frac in protocol['capacity_fractions_training_peak']:
            for name in lock['selected']:
                directory=out/f'seed_{seed}'/f'cap_{frac}'/name
                summary=json.load(open(directory/'summary.json'));cfg=json.load(open(directory/'config.json'))
                rows.append(dict(seed=seed,capacity_fraction=frac,capacity_kw=cfg['capacity'],policy=name,**summary))
                if frac==.35:
                    f=pd.read_csv(directory/'sessions.csv');f['seed']=seed;f['policy']=name;frames.append(f)
            oracle=json.load(open(out/f'seed_{seed}'/f'cap_{frac}'/'offline.json'))
            oracles.append(dict(seed=seed,capacity_fraction=frac,offline_delivered=oracle['delivered_bound']))
    scores=pd.DataFrame(rows);scores.to_csv(out/'test_scores.csv',index=False)
    oracles=pd.DataFrame(oracles);oracles.to_csv(tables/'offline_bounds.csv',index=False)
    for _,r in scores.iterrows():
        upper=oracles[(oracles.seed==r.seed)&(oracles.capacity_fraction==r.capacity_fraction)].offline_delivered.iloc[0]
        if r.delivered>upper+1e-6:raise AssertionError('causal policy exceeds offline bound')
    primary=scores[scores.capacity_fraction==.35].copy();frame=pd.concat(frames,ignore_index=True)
    numeric=['tail','mean_shortfall','delivered','cost_per_kwh','new_shortfall','repeat_failure','latency_p95']
    means=primary.groupby('policy')[numeric].mean().reindex(ORDER)
    means.to_csv(tables/'primary_means.csv')
    paired=[]
    for name in ORDER:
        a=primary[primary.policy==name].set_index('seed');b=primary[primary.policy==comparator].set_index('seed')
        for metric in ['tail','mean_shortfall','new_shortfall','delivered','cost_per_kwh']:
            v=a[metric]-b[metric] if metric not in ['delivered','cost_per_kwh'] else a[metric]/b[metric]
            paired.append(dict(policy=name,metric=metric,**paired_seed_interval(v)))
    intervals=pd.DataFrame(paired);intervals.to_csv(tables/'paired_intervals.csv',index=False)
    individual=primary.pivot(index='seed',columns='policy',values='tail');individual.to_csv(tables/'seed_tail_values.csv')
    tests={metric:intervals[(intervals.policy=='history')&(intervals.metric==metric)].iloc[0].to_dict() for metric in ['tail','delivered','cost_per_kwh','new_shortfall']}
    tests['mean_target_pass']=bool(tests['tail']['mean']<=-.05 and tests['delivered']['mean']>=.98 and tests['cost_per_kwh']['mean']<=1.03)
    tests['interval_target_pass']=bool(tests['tail']['high']<=-.05 and tests['delivered']['low']>=.98 and tests['cost_per_kwh']['high']<=1.03)
    dumps(out/'primary_conclusion.json',tests)
    # Strata retain denominators and avoid interpreting structural infeasibility as bias.
    strata=[]
    for field in ['cohort','dwell_band','request_band']:
        z=frame.copy()
        z['dwell_band']=pd.cut(z.dwell_hours,[0,3,6,24],labels=['<=3h','3-6h','>6h'])
        z['request_band']=pd.cut(z.requested,[0,15,25,np.inf],labels=['<=15kWh','15-25kWh','>25kWh'])
        g=z.groupby(['seed','policy',field],observed=True).agg(sessions=('sid','size'),users=('user','nunique'),shortfall=('shortfall','mean'),individual_unavoidable=('individual_unavoidable','mean')).reset_index()
        g=g.rename(columns={field:'stratum'});g['dimension']=field;strata.append(g)
    pd.concat(strata).to_csv(tables/'strata.csv',index=False)
    failures=[]
    for (seed,policy),g in frame.groupby(['seed','policy']):
        for threshold in [.8,.9,.95]:
            u=g.assign(fail=g.shortfall>1-threshold+1e-9).groupby('user').agg(frequency=('fail','mean'),count=('fail','size'))
            u=u[u['count']>=5]
            failures.append(dict(seed=seed,policy=policy,fulfillment_threshold=threshold,repeated_users=len(u),fraction_users_failing_half=float((u.frequency>=.5).mean())))
    pd.DataFrame(failures).to_csv(tables/'failure_thresholds.csv',index=False)
    # Conditional bootstrap with fixed realized history; deliberately secondary.
    a=frame[(frame.seed==11)&(frame.policy=='history')];b=frame[(frame.seed==11)&(frame.policy==comparator)]
    boot=paired_block_interval(a,b);dumps(tables/'conditional_block_interval.json',boot)
    forecast=pd.concat([pd.read_csv(out/f'seed_{seed}'/'forecast.csv').assign(seed=seed) for seed in protocol['seeds']])
    fs=forecast.groupby(['seed','model','lead_minutes']).agg(sessions=('sid','size'),events=('y','sum'),brier=('brier','mean'),logloss=('logloss','mean')).reset_index()
    fs.to_csv(tables/'forecast_scores.csv',index=False)
    forecast.groupby(['seed','model','lead_minutes','cohort']).agg(sessions=('sid','size'),events=('y','sum'),brier=('brier','mean'),logloss=('logloss','mean')).reset_index().to_csv(tables/'forecast_cohorts.csv',index=False)
    bins=np.array([0,.001,.002,.005,.01,.02,.04,.08,.2,.5,1.]);forecast['bin']=pd.cut(forecast.p,bins,include_lowest=True)
    reliability=forecast.groupby(['model','lead_minutes','bin'],observed=True).agg(predicted=('p','mean'),observed=('y','mean'),count=('y','size')).reset_index()
    reliability.to_csv(tables/'reliability.csv',index=False)
    # Publication figures; backing CSV files are the same data used for plotting.
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
    colors={'history':'#1c5d99','pf_mpc':'#202020','equal':'#888888','stochastic':'#b5651d','point':'#6b5399','maxmin':'#417b5a'}
    curve=scores.groupby(['policy','capacity_fraction'])[['tail','delivered','cost_per_kwh']].mean().reset_index();curve.to_csv(tables/'capacity_curve.csv',index=False)
    fig,ax=plt.subplots(figsize=(3.4,2.65),layout='constrained')
    for model in ['empirical','hazard','hazard_cal']:
        g=reliability[(reliability.model==model)&(reliability.lead_minutes==60)]
        ax.plot(g.predicted,g.observed,'o-',ms=3,label=model)
    ax.plot([0,.08],[0,.08],color='gray',ls=':');ax.set(xlabel='Predicted departure probability',ylabel='Observed departure frequency',xlim=(0,.08),ylim=(0,.08));ax.legend(fontsize=7);ax.text(.04,.075,f"{int(fs[(fs.model=='hazard_cal')&(fs.lead_minutes==60)].events.sum())} events / {int(fs[(fs.model=='hazard_cal')&(fs.lead_minutes==60)].sessions.sum()):,} sessions",fontsize=7,ha='center')
    fig.savefig(figdir/'calibration.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(3.4,2.65),layout='constrained');cdf=[]
    for name in ['equal','stochastic','pf_mpc','history']:
        u=frame[(frame.policy==name)&(frame.seed==11)].groupby('user').shortfall.agg(['mean','count']);u=u[u['count']>=5]
        x=np.sort(u['mean'].values);y=np.arange(1,len(x)+1)/len(x)
        ax.step(x*100,y,where='post',label=LABELS[name],color=colors[name]);cdf.extend([dict(policy=name,shortfall=xx,cdf=yy) for xx,yy in zip(x,y)])
    pd.DataFrame(cdf).to_csv(tables/'user_cdf_seed11.csv',index=False)
    ax.set(xlabel='User mean shortfall (%)',ylabel='Fraction of repeated users');ax.legend(fontsize=7)
    fig.savefig(figdir/'user_service.pdf');plt.close(fig)
    val=pd.read_csv(out/'validation_grid.csv')
    fig,ax=plt.subplots(figsize=(3.4,2.55),layout='constrained')
    for name in ['history','pf_mpc','point','stochastic','debt_share']:
        v=val[val.name==name];ax.scatter(v.cost_per_kwh,v['tail']*100,label=LABELS[name],s=25)
    ax.set(xlabel='Cost / delivered kWh ($)',ylabel='Worst-decile shortfall (%)');ax.legend(fontsize=6.5)
    fig.savefig(figdir/'validation_tradeoff.pdf');plt.close(fig)
    supplements=pd.read_csv(out/'supplement_scores.csv')
    supplements.groupby(['variant','policy'])[['tail','delivered','cost_per_kwh','new_shortfall']].mean().to_csv(tables/'supplement_means.csv')
    effects=[]
    for (variant,policy),g in supplements.groupby(['variant','policy']):
        baseline=primary[primary.policy==policy].set_index('seed')
        for metric in ['tail','delivered','new_shortfall']:
            v=g.set_index('seed')[metric]-baseline[metric]
            effects.append(dict(variant=variant,policy=policy,metric=metric,**paired_seed_interval(v)))
    pd.DataFrame(effects).to_csv(tables/'supplement_effects.csv',index=False)
    intervention=pd.DataFrame(effects);intervention=intervention[(intervention.variant.isin(['early','late','wide','narrow']))&(intervention.metric=='tail')].copy()
    fig,ax=plt.subplots(figsize=(3.4,2.4),layout='constrained');x=np.arange(len(intervention))
    ax.errorbar(x,100*intervention['mean'],yerr=np.array([100*(intervention['mean']-intervention.low),100*(intervention.high-intervention['mean'])]),fmt='o',capsize=3,color=colors['history'])
    ax.axhline(0,color='gray',ls=':');ax.set_xticks(x,intervention.variant);ax.set(ylabel='Tail change (percentage points)')
    fig.savefig(figdir/'interventions.pdf');plt.close(fig)
    # Machine-generated manuscript values prevent stale hand-copied results.
    macros={'HistTail':100*means.loc['history','tail'],'BaseTail':100*means.loc[comparator,'tail'],
      'TailDiff':100*tests['tail']['mean'],'TailLow':100*tests['tail']['low'],'TailHigh':100*tests['tail']['high'],
      'DeliveryRatio':100*tests['delivered']['mean'],'DeliveryLow':100*tests['delivered']['low'],'DeliveryHigh':100*tests['delivered']['high'],
      'CostRatio':100*tests['cost_per_kwh']['mean'],'CostLow':100*tests['cost_per_kwh']['low'],'CostHigh':100*tests['cost_per_kwh']['high'],
      'NewDiff':100*tests['new_shortfall']['mean'],'NewLow':100*tests['new_shortfall']['low'],'NewHigh':100*tests['new_shortfall']['high'],
      'MaxViolation':float(scores.max_violation.max()),'MaxLatency':float(scores.latency_p95.max()),
      'BlockLow':100*boot['low'],'BlockHigh':100*boot['high']}
    tex='\n'.join('\\newcommand{\\'+k+'}{'+f'{v:.2f}'+'}' for k,v in macros.items())+'\n'
    tex+='\\newcommand{\\TestSessions}{'+str(int(primary[primary.policy=='history'].sessions.sum()))+'}\n'
    tex+='\\newcommand{\\FallbackCount}{'+str(int(scores.fallbacks.sum()))+'}\n'
    Path('manuscript/generated.tex').write_text(tex)
    lines=[]
    for name,r in means.iterrows():
        lines.append(f"{LABELS[name]} & {r['tail']*100:.1f} & {r.mean_shortfall*100:.1f} & {r.delivered/1000:.2f} & {r.cost_per_kwh:.3f} & {r.new_shortfall*100:.1f} \\\\")
    Path('manuscript/main_table.tex').write_text('\n'.join(lines)+'\n'+r'\bottomrule'+'\n')
    # Readable detailed report, final interpretation derived rather than promised.
    display=means.copy();display['tail']=display['tail']*100;display['mean_shortfall']*=100;display['new_shortfall']*=100;display['delivered']/=1000
    display=display[['tail','mean_shortfall','delivered','cost_per_kwh','new_shortfall']].round(3).reset_index()
    display.columns=['Policy','Worst-tail %','Mean shortfall %','MWh','$/delivered kWh','Entrant shortfall %']
    verdict='The prespecified practical target was not met.' if not tests['interval_target_pass'] else 'The model-conditional interval criteria met the prespecified practical target.'
    direction='higher (worse)' if tests['tail']['mean']>0 else 'lower (better)'
    text=f'''# Experimental results

The [diagnostic analyses](diagnostics.md) describe the matched numerical comparisons, later forecast landmarks, and corrected request-update ordering. These exploratory analyses supplement the locked primary study.

{verdict} All numerical policy results below come from designed synthetic workloads. The real ACN discovery sample is used only for the separate coverage audit.

## Primary result

Validation selected `{comparator}` as the fairness comparator. The candidate's worst-decile user shortfall was {means.loc['history','tail']*100:.2f}% versus {means.loc[comparator,'tail']*100:.2f}%. The paired difference was {tests['tail']['mean']*100:.2f} percentage points ({direction}); the 95% t interval across five generated populations was [{tests['tail']['low']*100:.2f}, {tests['tail']['high']*100:.2f}]. The target required a reduction of at least five percentage points.

Mean paired delivery ratio was {tests['delivered']['mean']*100:.2f}% (95% interval [{tests['delivered']['low']*100:.2f}, {tests['delivered']['high']*100:.2f}]); unit-cost ratio was {tests['cost_per_kwh']['mean']*100:.2f}% ([{tests['cost_per_kwh']['low']*100:.2f}, {tests['cost_per_kwh']['high']*100:.2f}]). Entrant mean-shortfall difference was {tests['new_shortfall']['mean']*100:.2f} percentage points ([{tests['new_shortfall']['low']*100:.2f}, {tests['new_shortfall']['high']*100:.2f}]). Ratios average paired population ratios, not ratios of pooled totals.

{table_md(display)}

These are means across five replications at 0.35 times the training peak. Energy is mean MWh per replication. All session counts, per-seed values and other capacities are saved in `test_scores.csv`. The tail uses each policy's own ranking and a minimum of five sessions per user. No session-level significance test is used.

## Data coverage and pilot

The real-data adapter retained 12 of 26 discovery records, with eight users and no user having five sessions. Six records lacked identity, three crossed a local-day boundary, three had no full service slot after request availability, and two had ambiguous updates within one rounded slot. These are mutually exclusive primary exclusions; raw records are preserved. No empirical fairness result is inferred from this sample.

The validation pilot contained {len(val)} controller configurations. `validation_grid.csv` preserves every result, including configurations failing the delivery or unit-cost selection guardrails. Candidate parameters were gamma 40, lambda 4, rho 0.2; the matched point-history and no-history ablations also selected gamma 40. The primary comparator and all settings were locked before test evaluation.

## Uncertainty and structural limits

The seed-11 conditional five-day block bootstrap interval for the candidate-minus-comparator tail difference was [{boot['low']*100:.2f}, {boot['high']*100:.2f}] percentage points. This sensitivity resamples realized outcomes without rerunning service-history dynamics. It is not interchangeable with the primary interval across independently generated populations. Five replications offer limited precision and describe the specified generator family only.

`tables/strata.csv` reports requested-energy ranges, dwell-time ranges, training-defined variability groups, entrants and individual full-power infeasibility. The latter is only an individual physical lower bound; shared congestion can add further shortage. `tables/offline_bounds.csv` contains maximum aggregate energy under actual future arrivals and departures. Every causal run was checked against that bound; the oracle is never ranked as a deployable controller.

## Forecasting, ablations and interventions

`tables/forecast_scores.csv` and `tables/forecast_cohorts.csv` report Brier score, log loss, event counts and denominators at 30, 60 and 120 minutes from the one-hour landmark. This conditioning excludes sessions already disconnected. `tables/reliability.csv` contains all plotted bins; small bins are not evidence of calibrated probabilities.

`tables/supplement_means.csv` and `tables/supplement_effects.csv` retain calibration, empirical-distribution, horizon, earlier/later forecast, spread, shorter-stay and request-inflation results with no retuning. They are secondary analyses, not new primary hypotheses. A distribution spread transform reconditions on current survival and does not guarantee an unchanged conditional median. Error parity was not established and no real-world causal attribution is made.

## Correctness and computation

Across the {len(scores)} primary policy/capacity/population runs, {int(scores.fallbacks.sum())} fallback decisions were recorded. Maximum recorded numerical constraint excess was {scores.max_violation.max():.3g}; the largest per-run 95th-percentile decision latency was {scores.latency_p95.max():.4f} seconds. The tolerance is 1e-7 in the checked numerical units. Runtime includes Python planning overhead and concurrent workloads on this machine; it is not a production latency guarantee. The full action and continuous-plan trace is saved for the seed-11 primary pair; all runs save session outcomes, settings, aggregate diagnostics and history-dependent results. Other full decision traces can be generated by enabling `trace=True`.

A separate clean Python environment reproduces the primary seed-11 pair within the documented tolerance when `reproduction/verification.json` reports success. This is same-machine automated reproduction, not independent author validation. The test transcript and final manifest provide the actual status.

## Contribution decision

The evidence supports an inspectable comparison protocol and a bounded, model-conditional statement about history weighting under uncertain departures. It does not establish a new fairness algorithm, universal improvement, actual driver disadvantage, or grid protection. The manuscript should be evaluated as a controlled audit with an honest negative-result pathway. Independent novelty review and author sign-off remain necessary before any submission.
'''
    Path('docs/results_report.md').write_text(text)
    claimmap=[['Claim','Evidence'],['Primary tail contrast','results/tables/paired_intervals.csv; results/primary_conclusion.json'],['Every baseline and capacity','results/test_scores.csv'],['Data feasibility gate','results/data_audit.json; data/raw/ornl_metadata.json'],['Forecast quality','results/tables/forecast_scores.csv; results/tables/reliability.csv'],['Ablations and stresses','results/tables/supplement_effects.csv'],['Offline service upper bounds','results/tables/offline_bounds.csv'],['Leakage/physics checks','tests/test_core.py; results/clean_environment_tests.txt'],['Fresh-environment reproduction','results/reproduction/verification.json'],['Protocol freeze','config/protocol.json; results/protocol_lock.json; config/secondary_analysis_lock.json']]
    Path('docs/claim_evidence_map.md').write_text('# Claim-to-artifact map\n\n'+table_md(pd.DataFrame(claimmap[1:],columns=claimmap[0]))+'\n')
    print(verdict,tests)
