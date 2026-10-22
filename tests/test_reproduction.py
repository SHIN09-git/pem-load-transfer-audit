"""Regression checks for portable result comparison. Copyright 2026 JIN HANZHE; MIT."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest

import pandas as pd

spec = importlib.util.spec_from_file_location("public_reproduce", Path(__file__).resolve().parents[1] / "reproduce.py")
reproduce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reproduce)


class ComparisonRegressionTests(unittest.TestCase):
    # Recorded PtNano cycle 21, 60-minute start: the Haswell BLAS path changes
    # expanded-SSE R² by 1.19e-9 while coefficients and RMSE retain strict agreement.
    row = {"mea": "PtNano", "cycle": 21, "start_min": 60,
           "exp_r2": 0.0006852654742093, "exp_c": 0.5034093302175918,
           "exp_tau_h": 0.08269535156745106, "exp_rmse": 0.00022257005376324012,
           "exp_identifiable": False}

    def compare(self, right, filename="exponential_window_sensitivity.csv"):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            reference, work = root / "reference", root / "work"
            for base, data in ((reference, [self.row]), (work, [right])):
                (base / "02_processed").mkdir(parents=True)
                (base / "04_results").mkdir()
                pd.DataFrame(data).to_csv(base / "04_results" / filename, index=False)
            return reproduce.compare_tables(reference, work)

    def test_recorded_r2_roundoff_is_accepted_and_reported(self):
        changed = deepcopy(self.row)
        changed["exp_r2"] = 0.0006852666606302
        result = self.compare(changed)
        override = result["csv_files"][0]["absolute_tolerance_overrides"][0]
        self.assertEqual(override["column"], "exp_r2")
        self.assertGreater(override["max_absolute_difference"], 1e-9)

    def test_material_r2_change_is_rejected(self):
        changed = deepcopy(self.row)
        changed["exp_r2"] += 1e-5
        with self.assertRaisesRegex(ValueError, "exp_r2"):
            self.compare(changed)

    def test_parameter_change_is_not_excused(self):
        changed = deepcopy(self.row)
        changed["exp_c"] += 1e-7
        with self.assertRaisesRegex(ValueError, "exp_c"):
            self.compare(changed)

    def test_rmse_still_uses_strict_tolerance(self):
        changed = deepcopy(self.row)
        changed["exp_rmse"] += 1e-9
        with self.assertRaisesRegex(ValueError, "exp_rmse"):
            self.compare(changed)

    def test_exception_does_not_spread_to_other_tables(self):
        changed = deepcopy(self.row)
        changed["exp_r2"] = 0.0006852666606302
        with self.assertRaisesRegex(ValueError, "exp_r2"):
            self.compare(changed, "unrelated_results.csv")

    def test_changed_fit_decision_is_rejected(self):
        changed = deepcopy(self.row)
        changed["exp_identifiable"] = True
        with self.assertRaisesRegex(ValueError, "Label mismatch"):
            self.compare(changed)

    def test_new_missing_value_is_rejected(self):
        changed = deepcopy(self.row)
        changed["exp_r2"] = float("nan")
        with self.assertRaisesRegex(ValueError, "exp_r2"):
            self.compare(changed)


if __name__ == "__main__":
    unittest.main()
