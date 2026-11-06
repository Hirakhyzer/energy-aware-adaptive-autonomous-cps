# ECO-CPS: Energy-Aware Adaptive Autonomous Cyber-Physical Systems

**A reproducible, simulation-first research framework for joint sensor-duty, embedded CPU and autonomous-control adaptation.**

**Scope:** energy efficiency, resource-constrained embedded computing, autonomous control, deadline-aware decision making. No cyberattack modules or security-review automation are included.

> **Research boundary:** Results are synthetic, obtained from a reduced-order 2D kinematic robot model and illustrative component power parameters. They are **not measured hardware energy savings**, verified real-time guarantees, certified safety properties or proof of a globally optimal policy. The constraint guard operates only within the documented model.

## Research question

Can a battery-powered autonomous CPS reduce modeled **total mission energy** by jointly adapting sensor sampling, CPU operating point and control period/speed, compared with fixed and independently optimized strategies, while keeping modeled timing and tracking constraints satisfied?

## Implemented research capabilities

- Deterministic simulated mobile robot with waypoint navigation, noisy sensor estimates, actuator slip and heading disturbances.
- Energy accounting in **joules** for CPU active/idle time, CPU mode transitions, sensors, communication, actuation and electronics.
- Three embedded CPU modes (eco, balanced, performance), adaptive sensing intervals and control update intervals, and three speed factors.
- Feasibility filtering for computational deadlines, observation/control age and a transparent position-uncertainty proxy. Conservative fallback reports infeasibility rather than claiming success.
- Five ablation policies: `fixed`, `sensing_only`, `compute_only`, `control_only`, `joint`.
- Matched-seed paired experiments and machine-readable `benchmark.json`, `runs.csv` and `summary.csv` outputs, with experiment configuration fingerprint.
- Tests and GitHub Actions Python version matrix, plus a packaged CLI.

## Install and run

Requires Python 3.10+. The research simulator itself uses only the Python standard library.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
python -m pytest -q

eco-cps simulate --config configs/baseline.json --policy joint --out results/demo.json
eco-cps simulate --config configs/baseline.json --policy fixed
eco-cps benchmark --config configs/baseline.json --seeds 7 17 27 --out results/benchmark
eco-cps report --input results/benchmark
```

Alternative command: `python -m eco_cps simulate --policy joint` after installation.

`simulate` returns code 0 on mission completion and 2 on infeasible, failed or invalid scenarios; benchmark returns 0 when experiments are executed and saved even if some policies fail (failures remain explicit in results).

## Architecture

```text
Scenario + route + component parameters
             |
  Sensor sampling / state estimate ----> joint decision engine
             |                                 |
             |                    candidate feasibility guard
             |                                 |
             +<--- CPU mode, control period, speed factor
                                               |
                                      waypoint controller
                                               |
                                    physical robot + disturbances
                                               |
                                  energy and constraint ledger
                                               |
                              paired benchmark + JSON / CSV report
```

The enumerative joint policy chooses from 81 candidate settings per time step using an approximate energy-per-forward-metre score and a regularization term for sparse sampling/control. This is a **myopic heuristic**, not horizon-optimal MPC. Sampling/controller updates can be delayed but are bounded by configured age limits. CPU work and energy are computed in Gcycles/GHz and watts × seconds; sensor and radio event costs are in joules. See [energy model](docs/ENERGY_MODELS.md) and [methodology](docs/BENCHMARK_PROTOCOL.md).

## Experiments and evaluation

Run the baseline and sensitivity configuration:

```bash
eco-cps benchmark --config configs/baseline.json --out results/baseline
eco-cps benchmark --config configs/stress.json --out results/stress
```

Compare only **completed** missions for energy consumption; incomplete missions have `energy_per_completed_mission_j = null`. Also report completion rates, elapsed time, maximum/RMS path deviation, deadline misses, sensor count, controller updates, CPU switches and battery-reserve events. A lower energy result is not sufficient if the policy fails to finish the mission or violates constraints.

For research use, increase seeds, sweep model parameters and calibrate all component power parameters on actual hardware before making field-level claims. Results are not independently validated measurements.

## Repository layout

```text
src/eco_cps/             Python API and CLI
configs/                 Nominal and stress scenarios
tests/                   Determinism, geometry, constraints, CLI, and report tests
docs/                    Architecture, energy model, benchmark protocol, limitations
.github/workflows/ci.yml Automated install, tests and CLI smoke verification
results/                 Git-ignored generated artifacts
```

## Documentation

- [System architecture](docs/ARCHITECTURE.md)
- [Energy and computation models](docs/ENERGY_MODELS.md)
- [Benchmark protocol](docs/BENCHMARK_PROTOCOL.md)
- [Research questions and hypotheses](docs/RESEARCH_QUESTIONS.md)
- [Limitations and validation roadmap](docs/LIMITATIONS.md)

## Research integrity

All model coefficients are illustrative and inspectable. The benchmark does not fabricate hardware readings, and it does not claim the model proves robustness or safety of a real robot. Results from one synthetic scenario do not imply broader generalization. External dataset and hardware experiments are future work.

## License

MIT License. See [LICENSE](LICENSE).
