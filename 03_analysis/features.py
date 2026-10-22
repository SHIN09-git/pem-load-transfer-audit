"""Causal forecast features and GC-anchored endpoints for the fixed protocol."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
LOADS=np.array([.1,.25,.5,.75,1,2,3])

def tail(g, minutes):
    if g.empty:return None
    g=g.sort_values(['t_s','source_row']);end=g.t_s.max();cut=end-minutes*60
    z=g[g.t_s>=cut];t=z.t_s.to_numpy()/3600;v=z.h2.to_numpy()
    slope=float(np.polyfit(t-t.mean(),v,1)[0]) if len(z)>=3 and np.ptp(t)>0 else np.nan
    return dict(h2=float(z.h2.median()),h2_raw=float(z.h2_raw.median()),tail_slope=slope,tail_n=len(z),tail_cutoff_h=cut/3600,tail_first_h=z.t_s.min()/3600,last_gc_h=end/3600,first_gc_h=g.t_s.min()/3600,gc_span_h=(end-g.t_s.min())/3600,n_gc=len(g),temp_C=float(z.temp_C.median()),pressure_bar=float(z.pressure_bar.median()),voltage_V=float(z.voltage_V.median()),tail_sd=float(z.h2.std()),source_first_row=int(z.source_row.min()),source_last_row=int(z.source_row.max()),median_interval_s=float(g.t_s.diff().median()))

def exp_profile(g,start_s):
    z=g[g.t_s>=start_s+300]
    fail={'exp_status':'insufficient','exp_c':np.nan,'exp_tau_h':np.nan,'exp_identifiable':False}
    if len(z)<12 or (z.t_s.max()-z.t_s.min())<1800:return fail,None
    t=(z.t_s.to_numpy()-start_s)/3600;y=z.h2.to_numpy();taus=np.geomspace(.03,100,241)
    ee=np.exp(-t[:,None]/taus[None,:]);n=len(y);sy=y.sum();syy=y@y;se=ee.sum(0);see=(ee*ee).sum(0);sey=y@ee
    det=n*see-se**2;a=(n*sey-se*sy)/np.maximum(det,1e-20);c=(sy-a*se)/n
    # Exact 2-variable NNLS: interior and both boundary candidates.
    cs=np.stack([c,np.zeros_like(c),np.full_like(c,max(y.mean(),0))]);aa=np.stack([a,np.maximum(sey/see,0),np.zeros_like(a)])
    ss=syy+n*cs**2+aa**2*see[None,:]+2*cs*aa*se[None,:]-2*cs*sy-2*aa*sey[None,:]
    ss[(cs<0)|(aa<0)]=np.inf;ix=np.argmin(ss,axis=0);sse=ss[ix,np.arange(len(taus))];cc=cs[ix,np.arange(len(taus))];amp=aa[ix,np.arange(len(taus))]
    best=int(np.argmin(sse));support=sse<=max(sse[best]*1.10,sse[best]+1e-15)
    ratio=taus[support].max()/taus[support].min();span=np.ptp(cc[support]);boundary=bool(support[0] or support[-1] or cc[best]<1e-9 or amp[best]<1e-9)
    identifiable=bool(ratio<=3 and span<=.2*np.median(y) and not boundary)
    fit=cc[best]+amp[best]*np.exp(-t/taus[best]);sst=((y-y.mean())**2).sum()
    info=dict(exp_status='fit',exp_c=float(cc[best]),exp_amplitude=float(amp[best]),exp_tau_h=float(taus[best]),exp_tau_low_h=float(taus[support].min()),exp_tau_high_h=float(taus[support].max()),exp_c_low=float(cc[support].min()),exp_c_high=float(cc[support].max()),exp_rmse=float(np.sqrt(sse[best]/n)),exp_r2=float(1-sse[best]/sst) if sst else np.nan,exp_boundary=boundary,exp_identifiable=identifiable,exp_n=n,exp_observed_span_h=float(np.ptp(t)),exp_profile_ratio=float(ratio))
    return info,pd.DataFrame({'tau_h':taus,'c':cc,'amplitude':amp,'sse':sse,'relative_sse':sse/max(sse[best],1e-20),'support10pct':support})

def build():
    gc=pd.read_csv(ROOT/'02_processed'/'gc_observations.csv');st=pd.read_csv(ROOT/'02_processed'/'stages.csv');oc=pd.read_csv(ROOT/'02_processed'/'ocv_observations.csv')
    groups={(m,int(s)):g for (m,s),g in gc.groupby(['mea','segment_id'])};ocgroups={(m,int(s)):g for (m,s),g in oc.groupby(['mea','segment_id'])}
    empty=gc.iloc[:0];cyc=[];excluded=[];chars=[];profiles=[];expfits=[]
    for mea,s in st.groupby('mea',sort=False):
        s=s.sort_values('start_s');records=list(s.itertuples(index=False))
        for pos,h in enumerate(records):
            if h.phase!='CstC_12A':continue
            later=records[pos+1:];low=None
            for q in later:
                if q.phase=='CstC_1A':low=q;break
                if q.phase in ['CstC_12A','H2_char','CV_cycles','OCV']:break
            hi=groups.get((mea,h.segment_id),empty);lo=groups.get((mea,low.segment_id),empty) if low else empty
            if low is None or hi.empty or lo.empty:
                excluded.append(dict(mea=mea,high_counter=h.counter,high_segment=h.segment_id,low_segment=low.segment_id if low else None,reason='no_next_low' if low is None else 'no_high_gc' if hi.empty else 'no_low_gc'));continue
            assert hi.t_s.max()<=h.end_s<low.start_s<=lo.t_s.min()
            exp,profile=exp_profile(hi,h.start_s)
            expfits.append(dict(mea=mea,cycle=int(h.counter),high_time_h=h.end_s/3600,**exp))
            if profile is not None:
                profile.insert(0,'cycle',int(h.counter));profile.insert(0,'mea',mea);profiles.append(profile)
            prevoc=[q for q in records[:pos] if q.phase=='OCV'];ocs=prevoc[-1] if prevoc else None
            ocfeat=dict(ocv_end_V=np.nan,ocv_drop_V=np.nan,ocv_age_h=np.nan,pre_ocv_wait_h=np.nan,ocv_current_protocol=False,ocv_end_h=np.nan)
            if ocs:
                o=ocgroups[(mea,ocs.segment_id)];start=o[o.t_s<=ocs.start_s+2];end=o[o.t_s>=ocs.end_s-10]
                ocfeat=dict(ocv_end_V=float(end.voltage_V.median()),ocv_drop_V=float(start.voltage_V.median()-end.voltage_V.median()),ocv_age_h=(h.end_s-ocs.end_s)/3600,pre_ocv_wait_h=(h.start_s-ocs.end_s)/3600,ocv_current_protocol=(h.start_s-ocs.end_s)<60,ocv_end_h=ocs.end_s/3600)
            for win in [30,60]:
                th=tail(hi,win);tl=tail(lo,win)
                early=hi[(hi.t_s>=h.start_s+300)&(hi.t_s<=h.start_s+2100)]
                row=dict(mea=mea,cycle=int(h.counter),low_counter=int(low.counter),window_min=win,batch='PtC_Reference' if mea in ['PtC','Reference'] else 'PtNano_PtBlack',high_segment=h.segment_id,low_segment=low.segment_id,high_start_h=h.start_s/3600,forecast_h=h.end_s/3600,high_duration_h=(h.end_s-h.start_s)/3600,low_start_h=low.start_s/3600,low_end_h=low.end_s/3600,low_duration_h=(low.end_s-low.start_s)/3600,early_h2=float(early.h2.median()),**ocfeat,**exp)
                row.update({'high_'+k:v for k,v in th.items()});row.update({'low_'+k:v for k,v in tl.items()});row['lag_gc_h']=tl['last_gc_h']-th['last_gc_h'];row['high_gc_staleness_h']=row['forecast_h']-th['last_gc_h'];row['high_drop']=row['early_h2']-th['h2'];row['target']=tl['h2'];row['time_h']=th['last_gc_h']
                # Inputs are known by h.end_s. Low columns are endpoint/retrospective QA only.
                cyc.append(row)
        cg=gc[(gc.mea==mea)&gc.phase.eq('H2_char')].copy()
        j=cg.current_mA.to_numpy()/4000;idx=np.abs(j[:,None]-LOADS).argmin(axis=1);cg['load_Acm2']=LOADS[idx]
        assert np.max(abs(j-LOADS[idx]))<.03
        for (counter,load),g in cg.groupby(['counter','load_Acm2']):
            for win in [30,60]:chars.append(dict(mea=mea,characterization=int(counter),load_Acm2=load,window_min=win,**tail(g,win)))
    cf=pd.DataFrame(cyc);cf.to_csv(ROOT/'02_processed'/'cycles.csv',index=False)
    pd.DataFrame(chars).to_csv(ROOT/'02_processed'/'characterization_tails.csv',index=False)
    pd.DataFrame(excluded).to_csv(ROOT/'04_results'/'pair_exclusions.csv',index=False)
    pd.DataFrame(expfits).to_csv(ROOT/'04_results'/'exponential_fits.csv',index=False)
    pd.concat(profiles,ignore_index=True).to_csv(ROOT/'04_results'/'exponential_profiles.csv',index=False)
    summary={'pairs_per_window':cf.groupby(['mea','window_min']).size().to_dict().__str__(),'excluded':excluded,'median_gap_h':float(cf[cf.window_min==30].lag_gc_h.median()),'future_feature_violations':int((cf.high_last_gc_h>cf.forecast_h).sum()),'low_before_forecast_violations':int((cf.low_start_h<=cf.forecast_h).sum()),'GC_interval_s':gc.groupby('mea').t_s.apply(lambda t:float(t.diff().median())).to_dict()}
    (ROOT/'04_results'/'pairing_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':build()
