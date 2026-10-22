from pathlib import Path
import pandas as pd,numpy as np,json
from models import metrics
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'04_results'
f=pd.read_csv(R/'frozen_scores.csv');o=pd.read_csv(R/'online_scores.csv');ph=pd.read_csv(R/'phase_sensitivity_scores.csv');pr=pd.read_csv(R/'online_predictions.csv');ex=pd.read_csv(R/'exponential_window_sensitivity.csv')
key=(f.mea=='PtC')&(f.window_min==30)&(f.split=='primary')&(f.subset=='all_predictions')
print('FROZEN BLOCKS AND QUALITY\n',f[key&f.model.isin(['affine','time','time_high_slope'])][['model','block','quality','n','mae','bias']].to_string(index=False))
p=ph[(ph.window_min==30)&(ph.block=='all')&(ph.quality=='all')&(ph.subset=='non_calibration')]
phase_summary=p.groupby(['split','interval','model']).mae.agg(['min','median','max']).reset_index();phase_summary.to_csv(R/'phase_sensitivity_summary.csv',index=False)
print('PHASE SUMMARY\n',phase_summary.to_string(index=False))
common=[]
for (mea,win,split),d in pr.groupby(['mea','window_min','split']):
    d=d[d.is_eval];allow=[set(q.loc[~q.is_calibration,'cycle']) for _,q in d.groupby('interval')];ids=set.intersection(*allow)
    for (k,m),q in d.groupby(['interval','model']):
        v=q[q.cycle.isin(ids)];common.append(dict(mea=mea,window_min=win,split=split,interval=k,model=m,**metrics(v.target,v.prediction)))
pd.DataFrame(common).to_csv(R/'common_evaluation_cycles_scores.csv',index=False)
exp=[]
for (mea,start),q in ex.groupby(['mea','start_min']):
    v=q[q.time_h>=750];exp.append(dict(mea=mea,start_min=start,n=len(v),identified=int(v.exp_identifiable.sum()),c_median=float(v.exp_c.median()),tau_median=float(v.exp_tau_h.median()),rmse_median=float(v.exp_rmse.median())))
pd.DataFrame(exp).to_csv(R/'exponential_sensitivity_summary.csv',index=False)
print('EXP SENSITIVITY\n',pd.DataFrame(exp).to_string(index=False))
print('UNCERTAINTY\n',pd.read_csv(R/'measurement_uncertainty_scenarios.csv').to_string(index=False))
