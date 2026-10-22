import sys,unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'03_analysis'))
from analyze import online_once

class CausalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        z=pd.read_csv(ROOT/'02_processed'/'cycles.csv');cls.d=z[(z.mea=='PtC')&(z.window_min==30)].copy()
    def run_online(self,d):
        r,_=online_once(d,'primary',250,550,750,10,10);return pd.DataFrame(r)
    def test_hidden_labels_cannot_change_predictions(self):
        baseline=self.run_online(self.d);hidden=baseline.loc[~baseline.is_calibration,'cycle'].unique();d=self.d.copy();d.loc[d.cycle.isin(hidden),'target']*=7
        altered=self.run_online(d)
        np.testing.assert_allclose(baseline.prediction,altered.prediction,rtol=0,atol=0)
    def test_current_calibration_label_not_available_to_own_prediction(self):
        b=self.run_online(self.d);first=int(b[b.is_calibration].cycle.min());d=self.d.copy();d.loc[d.cycle==first,'target']*=7;a=self.run_online(d)
        np.testing.assert_allclose(b[b.cycle<=first].prediction,a[a.cycle<=first].prediction,rtol=0,atol=0)
        self.assertGreater(np.max(abs(b[b.cycle>first].prediction.to_numpy()-a[a.cycle>first].prediction.to_numpy())),1e-6)
    def test_future_metadata_not_used_as_features(self):
        b=self.run_online(self.d);d=self.d.copy();d['low_pressure_bar']=-9;d['low_temp_C']=999;d['low_duration_h']=999
        a=self.run_online(d);np.testing.assert_allclose(b.prediction,a.prediction,rtol=0,atol=0)
    def test_forecast_precedes_target_and_all_labels_are_past(self):
        self.assertTrue((self.d.forecast_h<self.d.low_start_h).all());r=self.run_online(self.d)
        self.assertTrue((r.max_label_end_h<r.forecast_h).all())
    def test_equal_label_budgets_across_models(self):
        r=self.run_online(self.d)
        self.assertTrue(r.groupby('cycle').n_revealed_before.nunique().eq(1).all())
        self.assertTrue(r.groupby('cycle').is_calibration.nunique().eq(1).all())

if __name__=='__main__':unittest.main(verbosity=2)
