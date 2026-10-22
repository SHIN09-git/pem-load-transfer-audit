"""Exploratory follow-up: effects of missing immediately preceding OCV and elapsed waiting."""
from pathlib import Path
import json
import pandas as pd,numpy as np
from models import fit_predict,metrics,FEATURES
ROOT=Path(__file__).resolve().parents[1]
FEATURES['time_high_wait']=['time_h','high_h2','pre_ocv_wait_h']
FEATURES['time_high_ocvflag']=['time_h','high_h2','ocv_current_protocol']
d=pd.read_csv(ROOT/'02_processed'/'cycles.csv');rows=[]
for (mea,win),z in d.groupby(['mea','window_min']):
    for split,lo,hi,te0 in [('primary',250,550,750),('all_early',0,550,750),('post_runin',500,800,1000)]:
        tr=z[z.time_h.between(lo,hi)];te=z[z.time_h>=te0]
        for subset in ['all','immediate_OCV_only']:
            a=tr if subset=='all' else tr[tr.ocv_current_protocol]
            b=te if subset=='all' else te[te.ocv_current_protocol]
            for model in ['affine','time','time_high_slope','time_high_wait','time_high_ocvflag']:
                p,_=fit_predict(model,a,b);rows.append(dict(mea=mea,window_min=win,split=split,subset=subset,model=model,n_train=len(a),**metrics(b.target,p)))
pd.DataFrame(rows).to_csv(ROOT/'04_results'/'history_sensitivity_scores.csv',index=False)
out=d[(d.window_min==30)&~d.ocv_current_protocol][['mea','cycle','time_h','pre_ocv_wait_h','high_h2','target']]
out.to_csv(ROOT/'04_results'/'cycles_without_immediate_OCV.csv',index=False)
print(pd.DataFrame(rows).query("mea=='PtC' and window_min==30").to_string(index=False))
