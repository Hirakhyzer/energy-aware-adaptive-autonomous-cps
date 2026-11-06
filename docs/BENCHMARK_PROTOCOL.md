# Paired reproducible benchmark protocol

## Comparators

- `fixed`: sampling every tick, performance CPU, control every tick, full nominal speed.
- `sensing_only`: sensor period may be 1, 2 or 4 ticks; CPU and control/speed remain fixed.
- `compute_only`: CPU may be eco, balanced or performance; sensor and control/speed remain fixed.
- `control_only`: controller period may be 1, 2 or 4, speed factor 0.70, 0.85 or 1.0; sensor and CPU remain fixed.
- `joint`: 3 sensing periods × 3 controller periods × 3 CPU modes × 3 speed factors = 81 candidates at each tick.

All adaptive comparators use the same heuristic objective over their restricted candidate sets; this is an ablation, not a comparison with globally optimal competing algorithms.

## Reproducibility

The benchmark precomputes scenario rows for each seed. Each comparator receives the same input sequence, route and configuration for that seed. Runs are sequential, deterministic and hardware-independent. `experiment_sha256` hashes sorted configuration, seed and policy metadata (excluding creation time). The JSON report includes creation time, all rows, and configuration; CSV files are simplified for external analysis. Generated results are git-ignored by default.

## Primary endpoints

1. **Completion rate**: successful runs / attempted runs.
2. **Mean mission energy, completed runs only**: average joules across successful missions. Missing on 0 successful runs.
3. **Mission completion time**: mean seconds among completed runs.
4. **Constraint violations**: deadline misses, tracking-limit failures, battery-reserve failures and infeasibility.
5. **Operational diagnostics**: RMS/max cross-track error, samples, controller updates, CPU switches, energy breakdown.

Never compare early-stopped runs' low consumed energy as a success. A policy with no completed missions has undefined `mean_energy_completed_j`, not zero energy.

The benchmark currently uses arithmetic means and sample standard deviations of energy among completed runs. It does **not** compute confidence intervals or significance tests automatically. Because completion rates can differ between policies, the completed-run mean alone is not a fair universal efficiency ranking. For serious studies, pre-register performance constraints and analyze the same-seed successful subset, completion probability and uncertainty across sufficiently many independent seeds.

## Recommended experiments

Run `configs/baseline.json` and `configs/stress.json`; add sweeps for deadline, sampling noise, CPU power parameters, path length, payload and reserve energy. Investigate sensitivity to the controller's sparse-update penalties and the energy-per-forward-metre objective. Tune policies only on a training scenario set, evaluate on held-out seeds and report negative results.

## Checks

Install and run `python -m pytest -q` then use the CLI smoke test commands in the README. CI runs these on a Python version matrix. CI tests code integrity, **not** hardware efficiency or field safety.
