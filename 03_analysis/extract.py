"""Streaming extraction; no forward fill or value-based removal of GC records."""
from pathlib import Path
import json,zipfile,hashlib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
MAP={'elapsed time in s':'t_s','Temp in degC':'temp_C','I in mA':'current_mA','E in V':'voltage_V','freq in Hz':'freq_Hz','Z_magnitude in Ohm':'Z_Ohm','Z_phase in deg':'phase_deg','conductivity in uS/cm':'conductivity_uScm','pressure in bar abs':'pressure_bar','H2_uncorrected in vol.%':'h2_raw','H2_corrected in vol.%':'h2','measurement_type':'phase','measurement_type_counter':'counter'}

def extract():
    archive=ROOT/'01_raw'/'pem_water_electrolysis_degradation_data.zip'
    md5=hashlib.md5(archive.read_bytes()).hexdigest()
    assert archive.stat().st_size==199357168 and md5=='b161b3a2eb0d655266bd13618da386a7'
    allgc=[];allocv=[];allst=[];aud=[]
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if not name.endswith('.csv'):continue
            mea=name.split('_')[0];last_key=None;seg=0;last_t=None;rows=0;backward=0;eqtimes=0;sg=[];gcs=[];ocs=[];miss={};invalid=0
            with z.open(name) as f:
                for c in pd.read_csv(f,chunksize=250000):
                    c=c.rename(columns=MAP)
                    c['source_row']=np.arange(rows+1,rows+len(c)+1)
                    key=c.phase.astype(str)+'|'+c.counter.astype(str)
                    changes=key.ne(key.shift());changes.iloc[0]=(key.iloc[0]!=last_key)
                    c['segment_id']=changes.cumsum()+seg
                    seg=int(c.segment_id.iloc[-1]);last_key=key.iloc[-1]
                    dt=np.diff(np.r_[last_t if last_t is not None else c.t_s.iloc[0],c.t_s.to_numpy()])
                    backward+=int((dt<0).sum());eqtimes+=int((dt[1:] ==0).sum())+int(last_t is not None and dt[0]==0)
                    last_t=float(c.t_s.iloc[-1]);rows+=len(c)
                    for v in ['pressure_bar','temp_C','conductivity_uScm','h2']:
                        miss[v]=miss.get(v,0)+int(c[v].isna().sum())
                    valid=c.h2.notna()
                    invalid+=int((valid & ((c.h2<0)|(c.h2>=100))).sum())
                    gcs.append(c.loc[valid].copy())
                    # OCV retained in full so endpoint and early-decay features can be recomputed.
                    ocs.append(c.loc[c.phase.eq('OCV'),['t_s','voltage_V','current_mA','temp_C','counter','segment_id','source_row']].copy())
                    sg.append(c.groupby('segment_id',sort=False).agg(phase=('phase','first'),counter=('counter','first'),start_s=('t_s','min'),end_s=('t_s','max'),n_raw=('t_s','size'),n_gc=('h2','count'),first_row=('source_row','min'),last_row=('source_row','max')))
            ss=pd.concat(sg).reset_index().groupby('segment_id',sort=False).agg(phase=('phase','first'),counter=('counter','first'),start_s=('start_s','min'),end_s=('end_s','max'),n_raw=('n_raw','sum'),n_gc=('n_gc','sum'),first_row=('first_row','min'),last_row=('last_row','max')).reset_index()
            gg=pd.concat(gcs,ignore_index=True);oo=pd.concat(ocs,ignore_index=True)
            for d in [ss,gg,oo]: d.insert(0,'mea',mea)
            allst.append(ss);allgc.append(gg);allocv.append(oo)
            ar=dict(mea=mea,raw_rows=rows,gc_rows=len(gg),backward_timestamps=backward,repeated_timestamps=eqtimes,invalid_h2=invalid,missing=miss,stage_counts=ss.phase.value_counts().to_dict(),last_h=last_t/3600,identical_consecutive_gc=int(gg.h2.diff().eq(0).sum()))
            aud.append(ar);print(json.dumps(ar,ensure_ascii=False),flush=True)
    pd.concat(allgc,ignore_index=True).to_csv(ROOT/'02_processed'/'gc_observations.csv',index=False)
    pd.concat(allocv,ignore_index=True).to_csv(ROOT/'02_processed'/'ocv_observations.csv',index=False)
    pd.concat(allst,ignore_index=True).to_csv(ROOT/'02_processed'/'stages.csv',index=False)
    (ROOT/'04_results'/'raw_audit.json').write_text(json.dumps({'zip_md5':md5,'zip_bytes':archive.stat().st_size,'files':aud},ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':extract()
