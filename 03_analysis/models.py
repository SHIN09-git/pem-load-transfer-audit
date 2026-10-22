"""Small, auditable estimators. Fit and standardization use revealed labels only."""
import numpy as np
from scipy.optimize import nnls

FEATURES={'affine':['high_h2'],'time':['time_h'],'time_high':['time_h','high_h2'],'high_slope':['high_h2','high_tail_slope'],'time_high_slope':['time_h','high_h2','high_tail_slope'],'time_ocv':['time_h','ocv_end_V'],'exp_asymptote_affine':['exp_c'],'high_ocv':['high_h2','ocv_end_V'],'time_high_history':['time_h','high_h2','ocv_end_V']}

def fit_predict(name,train,test):
    y=train.target.to_numpy(float)
    if name=='median':return np.full(len(test),np.median(y)),{'n':len(y),'value':float(np.median(y))}
    if name=='last_label':return np.full(len(test),y[-1]),{'n':len(y),'last_value':float(y[-1])}
    if name=='proportional':
        a=float(np.median(y/train.high_h2));return test.high_h2.to_numpy()*a,{'n':len(y),'ratio':a}
    if name=='faradaic_equal_net_flux':
        r=12*test.high_h2.to_numpy()/(100-test.high_h2.to_numpy());return 100*r/(1+r),{'n':0,'fixed_current_ratio':12}
    if name=='odds_affine_nonnegative':
        x=12*train.high_h2.to_numpy()/(100-train.high_h2.to_numpy());z=y/(100-y)
        scale=max(x.std(),1e-12);b,_=nnls(np.c_[np.ones(len(x)),x/scale],z)
        tx=12*test.high_h2.to_numpy()/(100-test.high_h2.to_numpy());pr=np.c_[np.ones(len(tx)),tx/scale]@b
        return 100*pr/(1+pr),{'n':len(y),'intercept_odds':float(b[0]),'scaled_slope':float(b[1]),'scale':scale}
    feats=FEATURES[name];x=train[feats].to_numpy(float);tx=test[feats].to_numpy(float)
    med=np.nanmedian(x,axis=0);med=np.where(np.isfinite(med),med,0)
    x=np.where(np.isfinite(x),x,med);tx=np.where(np.isfinite(tx),tx,med)
    mean=x.mean(0);sd=x.std(0);sd=np.where(sd>1e-12,sd,1)
    X=np.c_[np.ones(len(x)),(x-mean)/sd];T=np.c_[np.ones(len(tx)),(tx-mean)/sd]
    # Single-predictor affine/time reproduce the proposal's OLS. Multifeature
    # models use fixed ridge=1 without evaluating a tuning grid on test labels.
    alpha=1.0 if len(feats)>1 else 0.0
    penalty=np.diag([0]+[alpha]*len(feats));b=np.linalg.lstsq(X.T@X+penalty,X.T@y,rcond=None)[0]
    pred=T@b
    return pred,{'n':len(y),'features':feats,'coefs_standardized':b.tolist(),'mean':mean.tolist(),'sd':sd.tolist(),'imputation_median':med.tolist(),'ridge_alpha':alpha,'negative_predictions':int((pred<0).sum())}

def metrics(y,p):
    y=np.asarray(y);p=np.asarray(p);ok=np.isfinite(y)&np.isfinite(p);y=y[ok];p=p[ok];e=p-y
    if not len(y):return {'n':0,'mae':np.nan,'mdare_pct':np.nan,'bias':np.nan,'rmse':np.nan}
    return {'n':len(y),'mae':float(np.mean(abs(e))),'mdare_pct':float(np.median(abs(e)/y)*100),'bias':float(np.mean(e)),'rmse':float(np.sqrt(np.mean(e**2))),'underprediction_fraction':float(np.mean(e<0))}
