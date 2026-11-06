# Energy model: assumptions and units

Energy components are integrated as joules. For each discrete tick of duration `dt_s`, the ledger computes:

- CPU: `P_active * t_execution + P_idle * max(0, dt_s - t_execution)`; a CPU mode switch adds `0.004 J`. `t_execution = workload_gcycles / frequency_ghz`.
- Sensor: `0.04 W * dt_s` baseline draw plus `0.005 J` per pose sample.
- Communication: `0.001 J` per sent pose sample.
- Motor/actuator: `(3.5 W + 9.0 * v_mps² + 0.8 * omega_rps²) * dt_s` while tracking. The active actuator model is empirical-shaped but **not calibrated**, and assumes no regenerative energy.
- Electronics: `0.20 W * dt_s`.

CPU modes:

| Mode | Frequency (GHz) | Active (W) | Idle (W) |
| --- | ---: | ---: | ---: |
| eco | 0.65 | 0.80 | 0.10 |
| balanced | 1.20 | 1.55 | 0.16 |
| performance | 1.80 | 2.75 | 0.22 |

CPU model parameters, sensor event costs and motor coefficients are all **illustrative defaults**; different platforms may reverse the ranking of policies. The model does not represent voltage conversion efficiency, actuator thermal effects, frequency-transition latency, battery voltage sag, or stochastic hardware power measurements.

The battery state `capacity_j - sum(component energy)` is an energy budget, not an electrochemical SOC estimator. It is intentionally independent of electrical voltage and temperature. When remaining energy falls below reserve, the run stops and is recorded as incomplete.

## Feasibility model

The candidate guard checks a worst-case **current tick** execution time (not an all-future schedulability proof), maximum state-observation age, maximum control-command age, and a simple deterministic uncertainty proxy:

`error_proxy_m = sensor_noise_m + 0.11 * max_speed_mps * speed_factor * age_steps * dt_s`.

This proxy is neither a confidence interval nor a physics-derived bound on positioning error. Track real sampled lateral error separately. Candidate control settings are recomputed every tick; there is no guarantee of robust stability or forward invariance.

## Research validation roadmap

1. Calibrate per-mode CPU power and task execution time through onboard measurement and timed workloads.
2. Measure sensor power with duty cycling and cost of wake-up transitions.
3. Measure propulsion energy vs. speed, angular velocity, slope and payload.
4. Fit uncertainty calibration on real pose-estimation residuals.
5. Compare model predictions against held-out hardware traces before reporting physical energy-saving percentages.
