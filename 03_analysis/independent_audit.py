"""Independent stdlib CSV/median audit of selected tails directly from ZIP."""
from pathlib import Path
import csv,io,zipfile,json,statistics,hashlib
ROOT=Path(__file__).resolve().parents[1]

def run():
    with (ROOT/'02_processed'/'cycles.csv').open(encoding='utf-8',newline='') as f:cycles=list(csv.DictReader(f))
    selected=[]
    for mea in ['PtC','PtBlack','PtNano','Reference']:
        d=[x for x in cycles if x['mea']==mea and x['window_min']=='30']
        for at in [0,26,65,-1]:
            r=d[at]
            for side in ['high','low']:
                selected.append(dict(mea=mea,cycle=int(r['cycle']),side=side,segment=int(r[side+'_segment']),cut=float(r[side+'_tail_cutoff_h'])*3600,end=float(r[side+'_last_gc_h'])*3600,expected=float(r[side+'_h2']),expected_n=int(r[side+'_tail_n']),values=[]))
    with zipfile.ZipFile(ROOT/'01_raw'/'pem_water_electrolysis_degradation_data.zip') as z:
        for mea in ['PtC','PtBlack','PtNano','Reference']:
            entries=[r for r in selected if r['mea']==mea]
            with z.open(mea+'_dataset.csv') as b:
                f=io.TextIOWrapper(b,encoding='utf-8',newline='');reader=csv.DictReader(f)
                for r in reader:
                    y=r['H2_corrected in vol.%']
                    if not y:continue
                    t=float(r['elapsed time in s']);counter=int(r['measurement_type_counter']);phase=r['measurement_type']
                    for e in entries:
                        expected_phase='CstC_12A' if e['side']=='high' else 'CstC_1A'
                        if counter==e['cycle'] and phase==expected_phase and e['cut']-1e-7<=t<=e['end']+1e-7:e['values'].append(float(y))
            print('independent raw audit completed',mea,flush=True)
    for e in selected:
        e['actual_n']=len(e['values']);e['actual_median']=statistics.median(e.pop('values'))
        e['passed']=e['actual_n']==e['expected_n'] and abs(e['actual_median']-e['expected'])<1e-12
    assert all(e['passed'] for e in selected)
    (ROOT/'04_results'/'independent_raw_audit.json').write_text(json.dumps({'method':'stdlib csv reader and statistics.median; separate implementation, same agent','n_tails':len(selected),'all_passed':True,'tails':selected},ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':run()
