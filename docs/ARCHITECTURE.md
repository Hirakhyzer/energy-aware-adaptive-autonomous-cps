# Architecture and execution semantics

ECO-CPS is a small closed-loop experiment, not a production robot stack.

1. Pre-generate a time-indexed stochastic scenario with its own seed (CPU workload, plant slip, heading disturbance and sensor noise). Every benchmark policy uses that same sequence for a given seed. Policies have different arrival times, but they see matched exogenous events at the same simulation step.
2. On each `dt_s` time tick, enumerate allowed joint settings for the selected policy, predict whether the *current* task load meets the configured deadline and whether observation/control age and the uncertainty proxy are admissible.
3. Among currently feasible candidates, score approximate component energy per forward metre, penalize sparse sensing/controller updates and apply the lowest-score setting. This is myopic, without global mission optimality. The controller is evaluated only when its update is due.
4. A sampling event corrects the dead-reckoned position estimate using a noisy pose measurement. When no sample is taken, the estimator propagates with previously commanded velocity and turn rate.
5. A waypoint controller computes linear and angular velocity using the estimated pose, with bounded turn rate. The physical unicycle then advances with the scenario's slip and heading disturbance.
6. Integrate CPU/sensor/radio/actuator/electronics energy in joules, record deadline misses, cumulative energy, tracking error and optional time series. Abort if the tracking limit or battery reserve threshold is violated.
7. Mark completed missions by proximity to the last route waypoint; noncompletion is represented explicitly by `timeout`, `infeasible`, `battery_reserve`, or `tracking_limit`.

## CPU and time model

The CPU execution time for a tick is `workload_gcycles / frequency_ghz`. The workload is `complexity*(0.022 + (0.018 if sensor_due else 0) + (0.032 if control_due else 0))` giga-cycles. If it exceeds `min(deadline_s, dt_s)` the candidate is rejected. The fixed baseline uses the performance mode; feasibility checks still apply. The simulator uses discrete synchronous updates rather than a continuous preemptive scheduler. Overrunning work is charged to CPU energy even if it exceeds `dt_s`.

## Control / plant

A reduced-order 2D unicycle model integrates speed and angular rate using midpoint integration. Tracking error is Euclidean distance to the closest *segment* of the reference polyline, not a rigorous collision or obstacle-clearance guarantee. Sensor values are noisy and not equal to physical truth.

## Extension interfaces

A research extension could replace `make_scenario` with recorded telemetry, `_controller` with model predictive control, `select` with robust constrained optimization, and illustrative CPU and motor models with device-characterization curves. Keep clear units, versioned scenarios and paired-seed policies so later experiments remain comparable.
