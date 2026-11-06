"""Installable CLI for simulations, benchmarks and offline report summaries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .config import load_config
from .evaluation import benchmark, save_benchmark
from .policy import POLICY_NAMES
from .simulation import simulate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eco-cps", description="Energy-aware autonomous CPS research simulator")
    sub = parser.add_subparsers(dest="command", required=True)
    sim = sub.add_parser("simulate", help="run a reproducible closed-loop mission")
    sim.add_argument("--config", type=Path)
    sim.add_argument("--seed", type=int)
    sim.add_argument("--policy", choices=POLICY_NAMES, default="joint")
    sim.add_argument("--out", type=Path, help="write JSON trace and summary to a file")
    bench = sub.add_parser("benchmark", help="compare policies on matched stochastic scenarios")
    bench.add_argument("--config", type=Path)
    bench.add_argument("--seeds", type=int, nargs="+", default=[7, 17, 27])
    bench.add_argument("--out", type=Path, default=Path("results/benchmark"))
    report = sub.add_parser("report", help="display the summary of a saved benchmark")
    report.add_argument("--input", type=Path, required=True, help="directory or benchmark JSON file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "simulate":
            cfg = load_config(args.config, seed=args.seed)
            result = simulate(args.policy, cfg, record_trace=bool(args.out))
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({key: value for key, value in result.items() if key != "trace"}, indent=2))
            return 0 if result["completed"] else 2
        if args.command == "benchmark":
            cfg = load_config(args.config)
            outputs = save_benchmark(benchmark(cfg, seeds=args.seeds), args.out)
            print(json.dumps(outputs, indent=2))
            return 0
        location = args.input / "benchmark.json" if args.input.is_dir() else args.input
        data = json.loads(location.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "summary" not in data:
            raise ValueError("expected a benchmark report with a summary")
        print(json.dumps(data["summary"], indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"eco-cps: {exc}", file=sys.stderr)
        return 2
