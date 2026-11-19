"""Fair paired-policy benchmark and machine-readable experiment reporting."""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev
from typing import Iterable

from .config import ExperimentConfig
from .policy import POLICY_NAMES
from .simulation import make_scenario, simulate


def benchmark(cfg: ExperimentConfig | None = None, *, seeds: Iterable[int] = (7, 17, 27),
              policies: Iterable[str] = POLICY_NAMES) -> dict:
    cfg = (cfg or ExperimentConfig()).validated()
    seed_list, policy_list = tuple(seeds), tuple(policies)
    if not seed_list or not policy_list:
        raise ValueError("seeds and policies must be nonempty")
    if any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0
           for seed in seed_list):
        raise ValueError("benchmark seeds must be nonnegative integers")
    if len(seed_list) != len(set(seed_list)):
        raise ValueError("seeds must be unique")
    if any(not isinstance(policy, str) or policy not in POLICY_NAMES
           for policy in policy_list):
        raise ValueError("unknown benchmark policy")
    if len(policy_list) != len(set(policy_list)):
        raise ValueError("policies must be unique")

    rows = []
    for seed in seed_list:
        trial = replace(cfg, seed=seed).validated()
        scenario = make_scenario(trial)
        for policy in policy_list:
            rows.append(simulate(policy, trial, scenario=scenario))

    aggregates = []
    for policy in policy_list:
        subset = [row for row in rows if row["policy"] == policy]
        successful = [row for row in subset if row["completed"]]
        energies = [row["energy_total_j"] for row in successful]
        aggregates.append({
            "policy": policy,
            "trials": len(subset),
            "completed": len(successful),
            "completion_rate": len(successful) / len(subset),
            "mean_energy_completed_j": round(mean(energies), 6) if energies else None,
            "std_energy_completed_j": round(stdev(energies), 6) if len(energies) >= 2 else None,
            "mean_elapsed_completed_s": round(mean(row["elapsed_s"] for row in successful), 6) if successful else None,
            "total_deadline_misses": sum(row["deadline_misses"] for row in subset),
            "tracking_limit_failures": sum(row["status"] == "tracking_limit" for row in subset),
        })
    manifest = {
        "schema_version": "1.0",
        "tool": "eco_cps",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration": cfg.as_dict(),
        "seeds": list(seed_list),
        "policies": list(policy_list),
    }
    canonical = json.dumps({k: v for k, v in manifest.items() if k != "created_at_utc"}, sort_keys=True)
    manifest["experiment_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"manifest": manifest, "runs": rows, "summary": aggregates}


def save_benchmark(report: dict, directory: str | Path) -> dict[str, str]:
    """Reject incomplete reports before creating any output files."""
    if (not isinstance(report, dict) or
        not isinstance(report.get("manifest"), dict) or
        not isinstance(report.get("runs"), list) or not report["runs"] or
        not isinstance(report.get("summary"), list) or not report["summary"] or
        any(not isinstance(row, dict) for row in report["runs"] + report["summary"])):
        raise ValueError("benchmark report needs a manifest, nonempty runs and summary")
    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "benchmark.json"
    csv_path = out / "runs.csv"
    summary_path = out / "summary.csv"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run_keys = [key for key in report["runs"][0] if key != "energy_breakdown_j"]
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=run_keys)
        writer.writeheader()
        for row in report["runs"]:
            writer.writerow({key: row.get(key) for key in run_keys})
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(report["summary"][0]))
        writer.writeheader()
        writer.writerows(report["summary"])
    return {"json": str(report_path), "runs_csv": str(csv_path), "summary_csv": str(summary_path)}
