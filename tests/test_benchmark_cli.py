import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from eco_cps.config import ExperimentConfig
from eco_cps.evaluation import benchmark, save_benchmark


def test_paired_benchmark_report_and_aggregation(tmp_path):
    result = benchmark(ExperimentConfig(), seeds=(7, 17))
    assert len(result["runs"]) == 10
    assert len(result["summary"]) == 5
    assert {row["seed"] for row in result["runs"]} == {7, 17}
    assert all(row["trials"] == 2 for row in result["summary"])
    outputs = save_benchmark(result, tmp_path)
    assert all(Path(file).exists() for file in outputs.values())
    recovered = json.loads((tmp_path / "benchmark.json").read_text())
    assert recovered["manifest"]["experiment_sha256"] == result["manifest"]["experiment_sha256"]
    assert benchmark(ExperimentConfig(), seeds=(7, 17))["runs"] == result["runs"]


@pytest.mark.parametrize("seeds", [(), (1, 1)])
def test_invalid_benchmark_seeds(seeds):
    with pytest.raises(ValueError):
        benchmark(seeds=seeds)


def test_module_cli_smoke(tmp_path):
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "eco_cps"]
    env = {**os.environ, "PYTHONPATH": str(root / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    sim = subprocess.run(command + ["simulate", "--config", str(root / "configs/baseline.json"), "--policy", "joint"],
                         cwd=root, env=env, text=True, capture_output=True)
    assert sim.returncode == 0, sim.stderr
    assert json.loads(sim.stdout)["completed"]
    bench = subprocess.run(command + ["benchmark", "--seeds", "7", "17", "--out", str(tmp_path)],
                           cwd=root, env=env, text=True, capture_output=True)
    assert bench.returncode == 0, bench.stderr
    report = subprocess.run(command + ["report", "--input", str(tmp_path)],
                            cwd=root, env=env, text=True, capture_output=True)
    assert report.returncode == 0, report.stderr
    assert len(json.loads(report.stdout)) == 5
