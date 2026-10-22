"""Resolve the proposal's calibration boundary without replacing the main protocol."""
import pandas as pd
from pathlib import Path
from models import fit_predict,metrics
ROOT=Path(__file__).resolve().parents[1]
d=pd.read_csv(ROOT/'02_processed'/'cycles.csv');rows=[]
for (mea,win),g in d.groupby(['mea','window_min']):
    for axis in ['time_h','forecast_h','low_last_gc_h','low_end_h']:
        tr=g[g[axis].between(250,550)];te=g[g[axis]>=750]
        for model in ['proportional','affine','time','median']:
            pred,_=fit_predict(model,tr,te)
            rows.append(dict(mea=mea,window_min=win,split_axis=axis,model=model,n_train=len(tr),first_train_cycle=int(tr.cycle.min()),last_train_cycle=int(tr.cycle.max()),**metrics(te.target,pred)))
r=pd.DataFrame(rows);r.to_csv(ROOT/'04_results'/'proposal_reproduction.csv',index=False)
print(r[(r.window_min==30)&(r.model=='affine')].to_string(index=False))
