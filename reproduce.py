#!/usr/bin/env python3
"""Public reproduction entry point. Python 3.12; audit uses the standard library."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent
ARCHIVE = "pem_water_electrolysis_degradation_data.zip"
ANALYSIS = ["analyze.py", "reproduce_proposal.py", "robustness.py",
            "history_sensitivity.py", "summarize.py", "figures.py"]
EXPONENTIAL_R2_TABLES = {
    "02_processed/cycles.csv", "04_results/exponential_fits.csv",
    "04_results/exponential_window_sensitivity.csv",
}

def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with Path(path).open("rb") as f:
        while chunk := f.read(4 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False) + "\n", encoding="utf-8")

def verify_manifest(path, root):
    checked = 0
    for record in rows(path):
        target = (root / record["path"]).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError("Manifest path escapes the package")
        if target.stat().st_size != int(record["bytes"]) or digest(target) != record["sha256"]:
            raise ValueError("File integrity mismatch: " + record["path"])
        checked += 1
    return checked

def truth(value):
    if value not in ("True", "False"):
        raise ValueError("Unexpected boolean: " + value)
    return value == "True"

def metrics(data):
    errors = [(float(r["prediction"]) - float(r["target"]), float(r["target"])) for r in data]
    errors = [(e, y) for e, y in errors if math.isfinite(e) and math.isfinite(y)]
    n = len(errors)
    if not n:
        return {"n": 0, **{k: None for k in ["mae", "bias", "rmse", "mdare_pct", "underprediction_fraction"]}}
    return {"n": n, "mae": math.fsum(abs(e) for e, _ in errors) / n,
            "bias": math.fsum(e for e, _ in errors) / n,
            "rmse": math.sqrt(math.fsum(e * e for e, _ in errors) / n),
            "mdare_pct": statistics.median(abs(e) / y for e, y in errors) * 100,
            "underprediction_fraction": sum(e < 0 for e, _ in errors) / n}

def audit_tables(root):
    cycles = rows(root / "02_processed/cycles.csv")
    counts = {}
    seen = set()
    for row in cycles:
        key = (row["mea"], row["window_min"], row["cycle"])
        if key in seen:
            raise ValueError("Duplicate cycle/window")
        seen.add(key)
        count_key = row["mea"] + "/" + row["window_min"]
        counts[count_key] = counts.get(count_key, 0) + 1
        if not (float(row["high_last_gc_h"]) <= float(row["forecast_h"]) < float(row["low_start_h"])):
            raise ValueError("Invalid forecast chronology")
        if float(row["target"]) != float(row["low_h2"]):
            raise ValueError("Target differs from the subsequent low-load endpoint")
    expected = {m + "/" + w: n for m, n in [("PtC", 137), ("PtBlack", 136), ("PtNano", 137), ("Reference", 137)] for w in ["30", "60"]}
    if counts != expected or len(cycles) != 1094:
        raise ValueError("Unexpected cycle counts")
    score_rows_checked = 0
    budget_slots = {}
    highlights = {}
    for prefix, keys in [
        ("frozen", ["mea", "window_min", "split", "model"]),
        ("online", ["mea", "window_min", "split", "interval", "phase", "model"]),
        ("phase_sensitivity", ["mea", "window_min", "split", "interval", "phase", "model"]),
    ]:
        grouped = {}
        for row in rows(root / ("04_results/" + prefix + "_predictions.csv")):
            key = tuple(row[k] for k in keys)
            grouped.setdefault(key, []).append(row)
            if prefix != "frozen":
                if not float(row["max_label_end_h"]) < float(row["forecast_h"]):
                    raise ValueError("A revealed endpoint is not in the past")
                slot = (prefix, *(row[k] for k in keys if k != "model"), row["cycle"])
                budget = tuple(row[k] for k in ["n_initial", "n_revealed_before", "is_calibration", "max_label_end_h"])
                previous = budget_slots.setdefault(slot, budget)
                if budget != previous:
                    raise ValueError("Models have unequal label schedules")
        for s in rows(root / ("04_results/" + prefix + "_scores.csv")):
            selected = [r for r in grouped[tuple(s[k] for k in keys)] if truth(r["is_eval"])]
            if s["block"] == "early_late":
                selected = [r for r in selected if float(r["time_h"]) < 1100]
            elif s["block"] == "late":
                selected = [r for r in selected if float(r["time_h"]) >= 1100]
            elif s["block"] != "all":
                raise ValueError("Unknown time block")
            if s["quality"] != "all":
                field = {"known_high_quality": "high_quality",
                         "retrospective_both_quality": "both_quality"}[s["quality"]]
                selected = [r for r in selected if truth(r[field])]
            if s["subset"] == "non_calibration":
                selected = [r for r in selected if not truth(r["is_calibration"])]
            elif s["subset"] != "all_predictions":
                raise ValueError("Unknown scoring subset")
            actual = metrics(selected)
            for name, value in actual.items():
                stored = s.get(name, "")
                if value is None:
                    if stored not in ("", "nan"):
                        raise ValueError("Nonempty score for an empty subset")
                elif not stored or not math.isclose(float(stored), value, rel_tol=1e-10, abs_tol=1e-12):
                    raise ValueError("Score mismatch: " + prefix + "/" + name)
            score_rows_checked += 1
            if s["mea"] == "PtC" and s["window_min"] == "30" and s["quality"] == "all" and s["block"] == "all":
                if prefix == "frozen" and s["subset"] == "all_predictions":
                    highlights["frozen/" + s["split"] + "/" + s["model"]] = actual
                if prefix == "online" and s["split"] == "primary" and s["subset"] == "non_calibration":
                    highlights["online/every" + s["interval"] + "/" + s["model"]] = actual
    if highlights["frozen/primary/affine"]["n"] != 70 or highlights["frozen/primary/affine"]["underprediction_fraction"] != 1:
        raise ValueError("Primary Pt/C result changed")
    return {"cycle_rows": len(cycles), "pairs_per_window": 547, "counts": counts,
            "score_rows_recomputed": score_rows_checked,
            "equal_budget_prediction_slots": len(budget_slots), "ptc_results": highlights,
            "scope": "Standard-library recalculation from bundled predictions, not model refitting or independent experiments."}

def check_dependencies():
    expected = {"numpy": "2.3.5", "pandas": "3.0.1", "scipy": "1.18.1", "matplotlib": "3.11.2"}
    installed = {}
    for name, version in expected.items():
        try:
            installed[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            raise RuntimeError("Missing " + name + "; install requirements.txt in a Python 3.12 virtual environment")
        if installed[name] != version:
            raise RuntimeError(name + " version differs from the frozen environment; install requirements.txt")
    return installed

def check_archive(path, reference):
    if path.stat().st_size != reference["bytes"]:
        raise ValueError("Raw archive size mismatch")
    if digest(path, "md5") != reference["md5"] or digest(path) != reference["sha256"]:
        raise ValueError("Raw archive checksum mismatch")

def run_script(work, relative, log):
    print("Running " + relative, flush=True)
    started = time.monotonic()
    with log.open("w", encoding="utf-8") as f:
        result = subprocess.run([sys.executable, str(work / relative)], cwd=work,
                                stdout=f, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(relative + " failed; see " + str(log))
    return {"script": relative, "exit_code": result.returncode,
            "seconds": round(time.monotonic() - started, 3), "log": log.name}

def compare_tables(reference, work):
    """Compare every regenerated numeric cell and all labels; figures are regenerated separately."""
    import numpy as np
    import pandas as pd
    results = []
    numeric_mismatches = []
    for relative in sorted(
        [p.relative_to(reference) for p in (reference / "04_results").glob("*.csv")]
        + [p.relative_to(reference) for p in (reference / "02_processed").glob("*.csv")]
    ):
        left = pd.read_csv(reference / relative)
        right = pd.read_csv(work / relative)
        if list(left.columns) != list(right.columns) or left.shape != right.shape:
            raise ValueError("Table shape/header mismatch: " + str(relative))
        n_numeric = 0
        max_abs = 0.0
        tolerance_overrides = []
        for col in left:
            a, b = left[col], right[col]
            if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b) and not pd.api.types.is_bool_dtype(a):
                aa, bb = a.to_numpy(dtype=float), b.to_numpy(dtype=float)
                # Expanded SSE loses digits when divided by small within-window variance.
                # Keep all fit parameters/predictions strict; only this derived R² has an absolute floor.
                atol = 1e-8 if col == "exp_r2" and relative.as_posix() in EXPONENTIAL_R2_TABLES else 1e-12
                close = np.isclose(aa, bb, rtol=1e-9, atol=atol, equal_nan=True)
                if not close.all():
                    bad = np.flatnonzero(~close)
                    differences = np.abs(aa[bad] - bb[bad])
                    numeric_mismatches.append({
                        "path": relative.as_posix(), "column": col, "mismatches": int(len(bad)),
                        "max_absolute_difference": str(float(np.max(differences))),
                        "examples": [
                            {"row": int(i), "reference": str(aa[i]), "recomputed": str(bb[i]),
                             "keys": {k: str(left.iloc[i][k]) for k in
                                      ("mea", "cycle", "start_min", "window_min", "model", "split") if k in left}}
                            for i in bad[:3]]})
                finite = np.isfinite(aa) & np.isfinite(bb)
                if finite.any():
                    max_abs = max(max_abs, float(np.max(np.abs(aa[finite] - bb[finite]))))
                if atol != 1e-12:
                    tolerance_overrides.append({
                        "column": col, "atol": atol,
                        "max_absolute_difference": float(np.max(np.abs(aa[finite] - bb[finite]))) if finite.any() else 0.0})
                n_numeric += int(finite.sum())
            elif a.fillna("<NA>").astype(str).tolist() != b.fillna("<NA>").astype(str).tolist():
                raise ValueError("Label mismatch: " + str(relative) + "/" + col)
        results.append({"path": relative.as_posix(), "rows": len(left), "columns": len(left.columns),
                        "finite_numeric_cells": n_numeric, "max_absolute_difference": max_abs,
                        "absolute_tolerance_overrides": tolerance_overrides})
    if numeric_mismatches:
        raise ValueError("Numeric mismatches: " + json.dumps(numeric_mismatches, ensure_ascii=False))
    def compare_json(a, b, where):
        if isinstance(a, dict):
            if not isinstance(b, dict) or set(a) != set(b):
                raise ValueError("JSON keys differ: " + where)
            for key in a:
                compare_json(a[key], b[key], where + "/" + key)
        elif isinstance(a, list):
            if not isinstance(b, list) or len(a) != len(b):
                raise ValueError("JSON lists differ: " + where)
            for i, (x, y) in enumerate(zip(a, b)):
                compare_json(x, y, where + "/" + str(i))
        elif isinstance(a, (int, float)) and not isinstance(a, bool):
            if not isinstance(b, (int, float)) or not (math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12) or math.isnan(a) and math.isnan(b)):
                raise ValueError("JSON number differs: " + where)
        elif a != b:
            raise ValueError("JSON value differs: " + where)
    json_files = []
    for file in sorted((reference / "04_results").glob("*.json")):
        other = work / "04_results" / file.name
        compare_json(json.loads(file.read_text(encoding="utf-8")), json.loads(other.read_text(encoding="utf-8")), file.name)
        json_files.append(file.name)
    return {"csv_files": results, "json_files": json_files, "rtol": 1e-9, "atol": 1e-12,
            "exp_r2_atol": 1e-8, "exp_r2_tables": sorted(EXPONENTIAL_R2_TABLES),
            "note": "Analysis mode copies extraction-dependent tables; full mode regenerates all compared tables."}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["audit", "analysis", "full"], default="audit")
    parser.add_argument("--output", type=Path, help="New output directory; must not already exist")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--raw-archive", type=Path, help="Pinned 199357168-byte raw ZIP (full mode)")
    source.add_argument("--download", action="store_true", help="Download the pinned raw ZIP (full mode)")
    args = parser.parse_args()
    if args.mode != "full" and (args.raw_archive or args.download):
        parser.error("--raw-archive and --download require --mode full")
    if args.mode == "full" and not (args.raw_archive or args.download):
        parser.error("full mode requires --raw-archive FILE or --download")
    # Resolve integrity and dependencies before creating a working directory.
    manifest = ROOT / "MANIFEST_SHA256.csv"
    frozen = verify_manifest(ROOT / "provenance/FROZEN_SHA256.csv", ROOT)
    checked = verify_manifest(manifest, ROOT)
    packages = check_dependencies() if args.mode != "audit" else {}
    output = (args.output or ROOT / "reproductions" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6])).resolve()
    if output == ROOT or ROOT.is_relative_to(output):
        parser.error("Output cannot be the package root or its ancestor")
    output.mkdir(parents=True, exist_ok=False)
    report = {"status": "running", "mode": args.mode, "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "python": sys.version, "packages": packages, "manifest_files": checked, "frozen_files": frozen,
              "external_peer_review": False}
    started = time.monotonic()
    try:
        if args.mode == "audit":
            report["audit"] = audit_tables(ROOT)
        else:
            work = output / "workspace"
            work.mkdir()
            for dirname in ["00_admin", "03_analysis", "tests"]:
                shutil.copytree(ROOT / dirname, work / dirname)
            for dirname in ["01_raw", "02_processed", "04_results", "05_figures"]:
                (work / dirname).mkdir()
            if args.mode == "analysis":
                for dirname in ["02_processed", "04_results"]:
                    shutil.copytree(ROOT / dirname, work / dirname, dirs_exist_ok=True)
            else:
                source = json.loads((ROOT / "provenance/upstream_verification.json").read_text(encoding="utf-8"))["archive"]
                dest = work / "01_raw" / ARCHIVE
                if args.download:
                    temporary = dest.with_suffix(".zip.part")
                    print("Downloading pinned raw archive (199 MB)...", flush=True)
                    request = urllib.request.Request(source["url"], headers={"User-Agent": "pem-load-transfer-audit/1.0"})
                    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as out:
                        shutil.copyfileobj(response, out, 1024 * 1024)
                    check_archive(temporary, source)
                    temporary.rename(dest)
                else:
                    original = args.raw_archive.resolve()
                    check_archive(original, source)
                    shutil.copyfile(original, dest)
                    check_archive(dest, source)
                report["raw_archive"] = {k: source[k] for k in ["filename", "bytes", "md5", "sha256"]}
            steps = (["extract.py", "features.py"] if args.mode == "full" else []) + ANALYSIS
            report["steps"] = []
            logs = output / "logs"
            logs.mkdir()
            for script in steps:
                report["steps"].append(run_script(work, "03_analysis/" + script, logs / (script + ".log")))
            report["steps"].append(run_script(work, "tests/test_causality.py", logs / "causality.log"))
            if args.mode == "full":
                report["steps"].append(run_script(work, "03_analysis/independent_audit.py", logs / "independent_raw_audit.log"))
            report["comparison"] = compare_tables(ROOT, work)
            report["audit"] = audit_tables(work)
            report["figure_files_generated"] = sorted(p.name for p in (work / "05_figures").iterdir())
            if len(report["figure_files_generated"]) != 12:
                raise ValueError("Expected six PNG and six SVG figures")
            report["original_frozen_files_unchanged"] = verify_manifest(ROOT / "provenance/FROZEN_SHA256.csv", ROOT)
        report["status"] = "passed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        raise
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(output / "validation.json", report)
    print("PASS: " + args.mode + "; validation report: " + str(output / "validation.json"))

if __name__ == "__main__":
    main()

