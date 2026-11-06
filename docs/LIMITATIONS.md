# Scope, assumptions and limitations

- Simulation only: differential-drive-like unicycle kinematics; no collision avoidance, terrain, electrical model, motor saturation dynamics, external actors or certified control barrier.
- The CPU model uses an illustrative power/frequency table and aggregate task cycles. The controller and sensor processes are synchronous. There is no real RTOS, preemption or interrupt jitter.
- The uncertainty proxy is heuristic; no probabilistic coverage or robust stability result is claimed.
- Actuator power is a simple function of commanded speed/turn, not a calibrated motor efficiency map.
- The objective is a myopic, enumerative energy-per-metre surrogate and can sacrifice completion time. It is not joint global optimal control.
- The physics trajectory uses seeded disturbances and noisy sensor samples, but their distribution is an assumption, not a validated disturbance model.
- Tight deadlines and tracking thresholds may produce explicitly failed runs. Failed runs are never silently counted as successful or assigned a zero-energy mission.
- A GitHub Actions pass confirms code execution and tests under listed Python versions; it is not an engineering safety or empirical energy-efficiency certificate.

## Next research milestones

Calibration against embedded platform power traces; state-of-charge and motor-efficiency measurements; feedback-robust constrained optimization or MPC; complete WCET/RTOS analysis; realistic robot simulator or hardware-in-the-loop; statistical confidence intervals over independently sampled missions; reproducible cross-domain transfer study.
