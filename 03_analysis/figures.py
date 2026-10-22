from pathlib import Path
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'04_results';F=ROOT/'05_figures';F.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelsize':10,'legend.fontsize':8,'figure.dpi':130,'savefig.dpi':220,'axes.titleweight':'bold'})
colors={'affine':'#BB5344','time':'#327F9A','time_high_slope':'#735B99','last_label':'#AD7948','time_recent8':'#238875','time_high_slope_expanding':'#735B99','affine_offset_last':'#BB5344'}
def save(fig,name):
    fig.savefig(F/(name+'.png'),bbox_inches='tight');fig.savefig(F/(name+'.svg'),bbox_inches='tight');plt.close(fig)
c=pd.read_csv(ROOT/'02_processed'/'cycles.csv');d=c[(c.mea=='PtC')&(c.window_min==30)];fp=pd.read_csv(R/'frozen_predictions.csv');op=pd.read_csv(R/'online_predictions.csv')

fig,axs=plt.subplots(2,1,figsize=(9,6.3),sharex=True,gridspec_kw={'height_ratios':[1.4,1]})
ax=axs[0];ax.plot(d.time_h,d.target,'o',ms=2.5,color='#242F3B',label='Observed subsequent low load')
for model,label in [('affine','Frozen high-load affine'),('time','Frozen time trend'),('time_high_slope','Time + high level + slope')]:
    q=fp[(fp.mea=='PtC')&(fp.window_min==30)&(fp.split=='primary')&(fp.model==model)];ax.plot(q.time_h,q.prediction,color=colors[model],label=label,lw=1.7)
q=fp[(fp.mea=='PtC')&(fp.window_min==30)&(fp.split=='all_early')&(fp.model=='time')];ax.plot(q.time_h,q.prediction,'--',color='#238875',label='Time trend, all data up to 550 h')
ax.set_ylabel('Low-load H2 (vol.%)');ax.set_title('Pt/C: a fixed high-load proxy misses the later low-load trajectory',loc='left',pad=12);ax.legend(loc='upper left',ncol=2)
axs[1].plot(d.time_h,d.high_h2,'o-',ms=2,lw=.8,color=colors['affine'],label='High-load 30-min tail median');axs[1].plot(d.time_h,d.exp_c,'.',ms=3,color='#327F9A',label='Single-exponential fitted asymptote')
axs[1].set_ylabel('High-load H2 (vol.%)');axs[1].set_xlabel('High-load observation time (h)');axs[1].legend(loc='upper center',bbox_to_anchor=(.5,-.23),ncol=2,frameon=False)
for ax in axs:ax.axvspan(250,550,color='#327F9A',alpha=.10);ax.axvspan(750,1520,color='#DCAD58',alpha=.07);ax.grid(axis='y',alpha=.15)
fig.tight_layout();save(fig,'01_PtC_frozen_predictions')

s=pd.read_csv(R/'frozen_scores.csv');s=s[(s.mea=='PtC')&(s.quality=='all')&(s.block=='all')&(s.subset=='all_predictions')]
mods=['affine','time','time_high_slope','time_ocv','exp_asymptote_affine'];labels=['High affine','Time only','Time + high + slope','Time + OCV','Asymptote affine']
fig,axs=plt.subplots(1,3,figsize=(10,4.1),sharey=True)
for ax,split,title in zip(axs,['primary','all_early','post_runin'],['Calibration 250-550 h','Calibration up to 550 h','Calibration 500-800 h']):
    for w,shift,col in [(30,-.16,'#327F9A'),(60,.16,'#9DBFCC')]:
        q=s[(s.split==split)&(s.window_min==w)].set_index('model');ax.barh(np.arange(len(mods))+shift,[q.loc[m,'mae'] for m in mods],height=.29,color=col,label=f'{w}-min window')
    ax.set_title(title,fontsize=10);ax.set_xlabel('MAE (vol.% points)');ax.set_yticks(np.arange(len(mods)),labels);ax.invert_yaxis();ax.grid(axis='x',alpha=.15);ax.xaxis.set_major_locator(MaxNLocator(3))
handles,legendlabels=axs[0].get_legend_handles_labels();fig.legend(handles,legendlabels,loc='lower center',bbox_to_anchor=(.5,-.03),ncol=2,frameon=False);fig.suptitle('Calibration history matters more than adding high-load features',fontsize=13,fontweight='bold');fig.tight_layout();save(fig,'02_calibration_sensitivity')

fig,axs=plt.subplots(2,1,figsize=(9,6.2),sharex=True)
for ax,k in zip(axs,[10,20]):
    ax.plot(d.time_h,d.target,color='#242F3B',lw=1.4,label='Observed subsequent low load')
    for model,label in [('last_label','Last revealed low value'),('time_recent8','Recent-8 time trend'),('time_high_slope_expanding','Updated time + high + slope')]:
        q=op[(op.mea=='PtC')&(op.window_min==30)&(op.split=='primary')&(op.interval==k)&(op.model==model)];ax.plot(q.time_h,q.prediction,color=colors[model],lw=1.2,label=label)
        if model=='time_recent8':
            cal=q[q.is_calibration];ax.scatter(cal.time_h,cal.target,s=25,marker='s',facecolor='white',edgecolor='#242F3B',zorder=5,label='Low label revealed AFTER forecast')
    ax.set_xlim(550,1490);ax.set_ylim(.075,.19);ax.set_ylabel('Low-load H2 (vol.%)');ax.set_title(f'One revealed label every {k} eligible cycles',loc='left',fontsize=11);ax.axvline(750,color='#999',ls=':',lw=.8);ax.grid(axis='y',alpha=.15)
axs[0].legend(loc='upper left',ncol=2);axs[1].set_xlabel('High-load observation time (h)');fig.tight_layout();save(fig,'03_sparse_recalibration')

gc=pd.read_csv(ROOT/'02_processed'/'gc_observations.csv');ew=pd.read_csv(R/'exponential_window_sensitivity.csv');st=pd.read_csv(ROOT/'02_processed'/'stages.csv')
fig,axs=plt.subplots(1,2,figsize=(10,4.1))
cy=120;h=st[(st.mea=='PtC')&(st.phase=='CstC_12A')&(st.counter==cy)].iloc[0];g=gc[(gc.mea=='PtC')&(gc.segment_id==h.segment_id)];t=(g.t_s-h.start_s)/3600
axs[0].plot(t,g.h2,'o',color='#243644',ms=3,label='Observed GC')
for start,col in [(5,'#327F9A'),(60,'#BB5344')]:
    p=ew[(ew.mea=='PtC')&(ew.cycle==cy)&(ew.start_min==start)].iloc[0];tt=np.linspace(start/60,3,200);y=p.exp_c+p.exp_amplitude*np.exp(-(tt-(start-5)/60)/p.exp_tau_h)
    axs[0].plot(tt,y,color=col,label=f'Fit from {start} min');axs[0].axhline(p.exp_c,ls='--',color=col,alpha=.75)
axs[0].axvline(2,ls=':',color='#999');axs[0].set_title('Pt/C cycle 120: fit-window dependence',fontsize=11,loc='left');axs[0].set_xlabel('Time since high-load stage start (h)');axs[0].set_ylabel('H2 (vol.%)');axs[0].legend()
for start,col in [(5,'#327F9A'),(30,'#D6A04A'),(60,'#BB5344')]:
    q=ew[(ew.mea=='PtC')&(ew.start_min==start)];axs[1].plot(q.time_h,q.exp_c,'.-',ms=2,lw=.8,color=col,label=f'Fit from {start} min')
axs[1].set_title('Estimated asymptote across cycles',fontsize=11,loc='left');axs[1].set_xlabel('Operating time (h)');axs[1].set_ylabel('Fitted asymptote (vol.%)');axs[1].legend()
for ax in axs:ax.grid(axis='y',alpha=.15)
fig.tight_layout();save(fig,'04_exponential_model_dependence')

ps=pd.read_csv(R/'phase_sensitivity_scores.csv');ps=ps[(ps.window_min==30)&(ps.split=='primary')&(ps.quality=='all')&(ps.block=='all')&(ps.subset=='non_calibration')]
fig,ax=plt.subplots(figsize=(9,4));xx=[];ys=[];names=[]
for i,(model,label) in enumerate([('time_recent8','Recent-8 time'),('last_label','Last low value'),('time_high_slope_expanding','Time + high\n+ slope')]):
    for k in [10,20]:
        vals=ps[(ps.model==model)&(ps.interval==k)].mae.to_numpy();x=len(names)+1;xx.append(x);ys.append(vals);names.append(f'{label}\nEvery {k} cycles')
        ax.scatter(np.linspace(x-.16,x+.16,len(vals)),vals,color=colors[model],s=13,alpha=.8)
        ax.plot([x-.22,x+.22],[np.median(vals)]*2,color='#222',lw=2)
ax.set_xticks(xx,names,fontsize=9);ax.set_ylabel('Non-calibration MAE (vol.% points)');ax.set_title('Changing the reveal offset changes the apparent benefit',loc='left',pad=10);ax.grid(axis='y',alpha=.15);fig.tight_layout();save(fig,'05_reveal_offset_sensitivity')

ch=pd.read_csv(ROOT/'02_processed'/'characterization_tails.csv');fig,axs=plt.subplots(2,2,figsize=(9,6.2),sharex=True)
for ax,mea in zip(axs.flat,['PtC','PtBlack','PtNano','Reference']):
    q=ch[(ch.mea==mea)&(ch.window_min==30)&(ch.characterization>=4)]
    for load,col in [(.25,'#BB5344'),(3,'#327F9A')]:
        z=q[q.load_Acm2==load].sort_values('characterization');odds=z.h2/(100-z.h2);ax.plot(z.last_gc_h,odds/odds.iloc[0],'o-',color=col,ms=4,label=f'{load:g} A/cm2')
    ax.set_title('Pt/C' if mea=='PtC' else mea,loc='left');ax.set_ylabel('Response / characterization 4');ax.axhline(1,color='#999',lw=.6);ax.grid(axis='y',alpha=.15);ax.legend()
for ax in axs[1]:ax.set_xlabel('Actual GC endpoint time (h)')
fig.tight_layout();save(fig,'06_characterization_growth')
print('Six figures saved as PNG and SVG.',flush=True)
