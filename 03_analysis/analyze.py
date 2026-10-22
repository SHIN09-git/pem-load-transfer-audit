from pathlib import Path
import json,warnings
import numpy as np
import pandas as pd
from models import fit_predict,metrics

ROOT=Path(__file__).resolve().parents[1]
SPLITS=[('primary',250,550,750),('all_early',0,550,750),('post_runin',500,800,1000)]
FROZEN=['median','proportional','affine','time','time_high','high_slope','time_high_slope','time_ocv','high_ocv','time_high_history','odds_affine_nonnegative','faradaic_equal_net_flux','exp_asymptote_affine']
ONLINE=['last_label','time_expanding','time_recent8','affine_expanding','affine_offset_last','time_high_slope_expanding']

def flags(d,tr):
    ok=np.ones(len(d),dtype=bool)
    for side in ['high']:
        ok &= d[side+'_pressure_bar'].between(29.5,30.5).to_numpy()
        ok &= (d[side+'_temp_C']-tr[side+'_temp_C'].median()).abs().le(2).to_numpy()
        ok &= d[side+'_gc_span_h'].ge(1).to_numpy()&d[side+'_tail_n'].ge(4).to_numpy()
    both=ok.copy()
    both &= d.low_pressure_bar.between(29.5,30.5).to_numpy()&(d.low_temp_C-tr.low_temp_C.median()).abs().le(2).to_numpy()
    both &= d.low_gc_span_h.ge(3).to_numpy()&d.low_tail_n.ge(4).to_numpy()
    return ok,both

def score_frame(preds,groupkeys,output):
    out=[]
    for keys,d in preds.groupby(groupkeys,dropna=False,sort=False):
        base=dict(zip(groupkeys,keys if isinstance(keys,tuple) else [keys]))
        ev=d[d.is_eval]
        for block,z in [('all',ev),('early_late',ev[ev.time_h<1100]),('late',ev[ev.time_h>=1100])]:
            for quality,q in [('all',z),('known_high_quality',z[z.high_quality]),('retrospective_both_quality',z[z.both_quality])]:
                for subset,v in [('all_predictions',q),('non_calibration',q[~q.is_calibration])]:
                    out.append({**base,'block':block,'quality':quality,'subset':subset,**metrics(v.target,v.prediction)})
    pd.DataFrame(out).to_csv(ROOT/'04_results'/output,index=False)

def frozen(df):
    rows=[];coefs=[]
    for (mea,win),d in df.groupby(['mea','window_min']):
        d=d.sort_values('forecast_h')
        for split,lo,hi,testlo in SPLITS:
            tr=d[d.time_h.between(lo,hi)];te=d[d.time_h>=testlo].copy()
            assert tr.low_end_h.max()<te.forecast_h.min()
            hq,bq=flags(te,tr)
            for model in FROZEN:
                pred,pars=fit_predict(model,tr,te)
                coefs.append(dict(mea=mea,window_min=win,split=split,model=model,params=pars))
                for n,(_,r) in enumerate(te.iterrows()):rows.append(dict(mea=mea,window_min=win,split=split,model=model,cycle=int(r.cycle),time_h=r.time_h,forecast_h=r.forecast_h,target=r.target,prediction=pred[n],n_train=len(tr),is_eval=True,is_calibration=False,high_quality=hq[n],both_quality=bq[n]))
    out=pd.DataFrame(rows);out.to_csv(ROOT/'04_results'/'frozen_predictions.csv',index=False)
    score_frame(out,['mea','window_min','split','model'],'frozen_scores.csv')
    (ROOT/'04_results'/'frozen_coefficients.json').write_text(json.dumps(coefs,ensure_ascii=False,indent=2),encoding='utf-8')

def online_once(d,split,lo,hi,testlo,k,phase):
    tr=d[d.time_h.between(lo,hi)].copy();future=d[d.time_h>hi].copy();hq,bq=flags(future,tr)
    history=tr.copy();rows=[];reveals=[];frozen_affine,_=fit_predict('affine',tr,future)
    for i,(_,r) in enumerate(future.iterrows()):
        current=future.iloc[[i]]
        # All visible past endpoints must have finished at prediction time.
        assert history.low_end_h.max()<r.forecast_h
        cal=(i+1-phase)%k==0
        for model in ONLINE:
            if model=='affine_offset_last':
                last=history.iloc[[-1]];lastp,_=fit_predict('affine',tr,last)
                prediction=float(frozen_affine[i]+last.target.iloc[0]-lastp[0])
            else:
                base=model.replace('_expanding','').replace('_recent8','')
                used=history.iloc[-8:] if model=='time_recent8' else history
                pp,_=fit_predict(base,used,current);prediction=float(pp[0])
            rows.append(dict(mea=r.mea,window_min=r.window_min,split=split,interval=k,phase=phase,model=model,cycle=int(r.cycle),time_h=r.time_h,forecast_h=r.forecast_h,target=r.target,prediction=prediction,n_initial=len(tr),n_revealed_before=len(history)-len(tr),max_label_end_h=float(history.low_end_h.max()),is_eval=r.time_h>=testlo,is_calibration=cal,high_quality=hq[i],both_quality=bq[i]))
        # Reveal only AFTER every model has predicted this cycle.
        if cal:
            history=pd.concat([history,current],ignore_index=True)
            reveals.append(dict(mea=r.mea,window_min=r.window_min,split=split,interval=k,phase=phase,cycle=int(r.cycle),label_available_h=float(r.low_end_h)))
    return rows,reveals

def online(df):
    rows=[];reveal=[];phase_rows=[]
    for (mea,win),d in df.groupby(['mea','window_min']):
        d=d.sort_values('forecast_h')
        for split,lo,hi,testlo in SPLITS:
            for k in [10,20]:
                rr,rv=online_once(d,split,lo,hi,testlo,k,k);rows+=rr;reveal+=rv
                # All reveal offsets tested only as sensitivity, not model tuning.
                if mea=='PtC' and split in ['primary','all_early']:
                    phase_rows+=rr
                    for phase in range(1,k):
                        r2,_=online_once(d,split,lo,hi,testlo,k,phase);phase_rows+=r2
        print('online finished',mea,win,flush=True)
    out=pd.DataFrame(rows);out.to_csv(ROOT/'04_results'/'online_predictions.csv',index=False)
    pd.DataFrame(reveal).to_csv(ROOT/'04_results'/'online_label_schedule.csv',index=False)
    score_frame(out,['mea','window_min','split','interval','phase','model'],'online_scores.csv')
    pp=pd.DataFrame(phase_rows);pp.to_csv(ROOT/'04_results'/'phase_sensitivity_predictions.csv',index=False)
    score_frame(pp,['mea','window_min','split','interval','phase','model'],'phase_sensitivity_scores.csv')

def characterization():
    d=pd.read_csv(ROOT/'02_processed'/'characterization_tails.csv');d['odds']=d.h2/(100-d.h2);rows=[]
    for (mea,win),z in d.groupby(['mea','window_min']):
        for ref in [2,4]:
            a=z[z.characterization==ref].set_index('load_Acm2');b=z[z.characterization==8].set_index('load_Acm2');ratio=(b.odds/a.odds)
            rows.append(dict(mea=mea,window_min=win,reference_characterization=ref,low_growth=ratio.loc[.25],high_growth=ratio.loc[3],ratio_of_growth=ratio.loc[.25]/ratio.loc[3],low_ref=a.loc[.25,'h2'],low_final=b.loc[.25,'h2'],high_ref=a.loc[3,'h2'],high_final=b.loc[3,'h2']))
    pd.DataFrame(rows).to_csv(ROOT/'04_results'/'load_growth_factors.csv',index=False)

if __name__=='__main__':
    warnings.filterwarnings('ignore',message='All-NaN slice encountered')
    df=pd.read_csv(ROOT/'02_processed'/'cycles.csv')
    frozen(df);characterization();online(df)
