from pathlib import Path
import json
import numpy as np
import pandas as pd
from models import fit_predict,metrics
from features import exp_profile
ROOT=Path(__file__).resolve().parents[1]

def block_bootstrap(y,a,b,block,seed=20261012,nboot=3000):
    """Paired moving-block resampling of this single observed trajectory only."""
    y=np.array(y);ea=abs(np.array(a)-y);eb=abs(np.array(b)-y);n=len(y);rng=np.random.default_rng(seed)
    starts=rng.integers(0,max(n-block+1,1),size=(nboot,int(np.ceil(n/block))))
    ids=(starts[:,:,None]+np.arange(min(block,n))[None,None,:]).reshape(nboot,-1)[:,:n]
    ma=ea[ids].mean(1);mb=eb[ids].mean(1);diff=ma-mb;gain=1-ma/mb
    return dict(n=n,block_cycles=block,mae_candidate=float(ea.mean()),mae_baseline=float(eb.mean()),mae_difference=float(ea.mean()-eb.mean()),difference_p025=float(np.quantile(diff,.025)),difference_p975=float(np.quantile(diff,.975)),relative_gain=float(1-ea.mean()/eb.mean()),gain_p025=float(np.quantile(gain,.025)),gain_p975=float(np.quantile(gain,.975)))

def comparisons():
    op=pd.read_csv(ROOT/'04_results'/'online_predictions.csv');fp=pd.read_csv(ROOT/'04_results'/'frozen_predictions.csv');rows=[]
    for (mea,win,split,k,phase),d in op.groupby(['mea','window_min','split','interval','phase']):
        # Keep calibration-cycle errors visible, but primary comparison omits them.
        d=d[d.is_eval & ~d.is_calibration];pv=d.pivot(index='cycle',columns='model',values='prediction');truth=d.groupby('cycle').target.first();t=d.groupby('cycle').time_h.first()
        for model in ['time_expanding','time_high_slope_expanding','affine_expanding','affine_offset_last','last_label']:
            for block in [5,10]:
                rows.append(dict(mea=mea,window_min=win,split=split,interval=k,phase=phase,candidate=model,baseline='time_recent8',comparison='online_same_budget',**block_bootstrap(truth,pv[model],pv.time_recent8,block)))
        f=fp[(fp.mea==mea)&(fp.window_min==win)&(fp.split==split)]
        for baseline in ['affine','time']:
            fz=f[f.model==baseline].set_index('cycle').loc[pv.index]
            for block in [5,10]:rows.append(dict(mea=mea,window_min=win,split=split,interval=k,phase=phase,candidate='time_recent8',baseline=baseline,comparison='online_vs_frozen_same_cycles_different_budget',**block_bootstrap(truth,pv.time_recent8,fz.prediction,block)))
    pd.DataFrame(rows).to_csv(ROOT/'04_results'/'paired_block_comparisons.csv',index=False)
    # Fixed-model paired comparison: direct 30% planning gate against time baseline.
    rr=[]
    for (mea,win,split),d in fp.groupby(['mea','window_min','split']):
        pv=d.pivot(index='cycle',columns='model',values='prediction');y=d.groupby('cycle').target.first()
        for model in ['time_high_slope','time_high','time_ocv','high_slope','exp_asymptote_affine']:
            for block in [5,10]:rr.append(dict(mea=mea,window_min=win,split=split,candidate=model,baseline='time',**block_bootstrap(y,pv[model],pv.time,block)))
    pd.DataFrame(rr).to_csv(ROOT/'04_results'/'frozen_block_comparisons.csv',index=False)

def exponential_sensitivity():
    gc=pd.read_csv(ROOT/'02_processed'/'gc_observations.csv');st=pd.read_csv(ROOT/'02_processed'/'stages.csv');rows=[]
    groups={(m,int(s)):g for (m,s),g in gc.groupby(['mea','segment_id'])}
    for h in st[st.phase.eq('CstC_12A')].itertuples(index=False):
        if (h.mea,h.segment_id) not in groups:continue
        g=groups[(h.mea,h.segment_id)]
        for start_min in [5,30,60]:
            # exp_profile removes first 5 minutes relative to supplied origin.
            # Shift origin together with removal; c and tau are invariant in the assumed family.
            p,_=exp_profile(g,h.start_s+(start_min-5)*60)
            rows.append(dict(mea=h.mea,cycle=h.counter,time_h=h.end_s/3600,start_min=start_min,**p))
    d=pd.DataFrame(rows);d.to_csv(ROOT/'04_results'/'exponential_window_sensitivity.csv',index=False)
    # Test auxiliary dynamic-shape predictability within the high hold, without low labels.
    rr=[]
    for h in st[st.phase.eq('CstC_12A')].itertuples(index=False):
        if (h.mea,h.segment_id) not in groups:continue
        g=groups[(h.mea,h.segment_id)];early=g[g.t_s<=h.start_s+3600];late=g[g.t_s>=h.start_s+5400]
        if len(late)<5:continue
        p,_=exp_profile(early,h.start_s)
        if p['exp_status']!='fit':continue
        pred=p['exp_c']+p['exp_amplitude']*np.exp(-(late.t_s.to_numpy()-h.start_s)/3600/p['exp_tau_h'])
        last=float(early.h2.iloc[-1]);base=np.full(len(late),last)
        rr.append(dict(mea=h.mea,cycle=h.counter,time_h=h.end_s/3600,exp_mae=metrics(late.h2,pred)['mae'],last_high_mae=metrics(late.h2,base)['mae'],early_exp_c=p['exp_c'],early_exp_tau_h=p['exp_tau_h'],early_identifiable=p['exp_identifiable']))
    pd.DataFrame(rr).to_csv(ROOT/'04_results'/'high_internal_forecast.csv',index=False)

def measurement_sensitivity():
    c=pd.read_csv(ROOT/'02_processed'/'cycles.csv');g=pd.read_csv(ROOT/'02_processed'/'gc_observations.csv');rows=[]
    for mea,d in c[c.window_min==30].groupby('mea'):
        late=d[d.time_h>=750];raw=g[(g.mea==mea)&g.phase.eq('CstC_1A')&(g.t_s>=750*3600)]
        factor=float(np.median(raw.h2/raw.h2_raw));tr=d[d.time_h.between(250,550)];p,_=fit_predict('affine',tr,late);err=late.target.to_numpy()-p
        rows.append(dict(mea=mea,low_correction_factor_median=factor,low_bias_corrected_pp=float(np.median(err)),raw_equivalent_bias_pp=float(np.median(err)/factor),raw_equivalent_bias_ppm=float(np.median(err)/factor*10000),high_tail_sd_median=float(late.high_tail_sd.median()),low_tail_sd_median=float(late.low_tail_sd.median()),note='equivalent additive low-channel drift scenario, not measured instrument uncertainty'))
    pd.DataFrame(rows).to_csv(ROOT/'04_results'/'measurement_uncertainty_scenarios.csv',index=False)

if __name__=='__main__':
    comparisons();exponential_sensitivity();measurement_sensitivity()
    print('Paired-block comparisons, exponential sensitivity and uncertainty scenarios saved.',flush=True)
