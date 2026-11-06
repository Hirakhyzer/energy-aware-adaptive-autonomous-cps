"""Closed-loop differential-drive-like unicycle simulation and energy ledger."""
from __future__ import annotations

from dataclasses import dataclass
import json
from math import atan2, hypot, sqrt
from random import Random

from .config import ExperimentConfig
from .model import Pose, advance, clip, cross_track_error, cpu_energy_j, motor_power_w, wrap_angle
from .policy import POLICY_NAMES, select


@dataclass(frozen=True)
class ScenarioStep:
    complexity: float
    slip: float
    turn_noise_rps: float
    measurement_x_m: float
    measurement_y_m: float
    measurement_heading_rad: float


def make_scenario(cfg: ExperimentConfig) -> tuple[ScenarioStep, ...]:
    """Pre-generate stochastic inputs once so every policy sees matched exogenous noise."""
    rng = Random(cfg.seed)
    rows = []
    for step in range(cfg.max_steps):
        fraction = step / cfg.max_steps
        complexity = 1.45 if 0.25 <= fraction < 0.60 else (1.25 if 0.75 <= fraction < 0.90 else 1.0)
        rows.append(ScenarioStep(
            complexity=complexity,
            slip=clip(1.0 + rng.gauss(0.0, cfg.slip_sigma), 0.70, 1.15),
            turn_noise_rps=rng.gauss(0.0, cfg.turn_noise_rps),
            measurement_x_m=rng.gauss(0.0, cfg.sensor_noise_m),
            measurement_y_m=rng.gauss(0.0, cfg.sensor_noise_m),
            measurement_heading_rad=rng.gauss(0.0, cfg.heading_noise_rad),
        ))
    return tuple(rows)


def _controller(estimate: Pose, target: tuple[float, float], cfg: ExperimentConfig, speed_factor: float) -> tuple[float, float]:
    desired = atan2(target[1] - estimate.y_m, target[0] - estimate.x_m)
    error = wrap_angle(desired - estimate.heading_rad)
    turn = clip(2.7 * error, -cfg.max_turn_rps, cfg.max_turn_rps)
    speed = cfg.max_speed_mps * speed_factor * clip(1.0 - abs(error) * 0.50, 0.25, 1.0)
    return speed, turn


def _waypoint(estimate: Pose, index: int, cfg: ExperimentConfig) -> int:
    while index < len(cfg.path_m) - 1 and estimate.distance_to(cfg.path_m[index]) <= cfg.goal_radius_m:
        index += 1
    return index


def simulate(policy: str = "joint", cfg: ExperimentConfig | None = None,
             *, record_trace: bool = False, scenario: tuple[ScenarioStep, ...] | None = None) -> dict:
    cfg = (cfg or ExperimentConfig()).validated()
    if policy not in POLICY_NAMES:
        raise ValueError(f"unknown policy: {policy}")
    disturbance = scenario if scenario is not None else make_scenario(cfg)
    if len(disturbance) < cfg.max_steps:
        raise ValueError("scenario is shorter than max_steps")

    physical = Pose(*cfg.path_m[0], 0.0)
    estimate = physical
    waypoint = 1
    speed, turn = 0.0, 0.0
    last_sensor, last_control = -1000, -1000
    previous_cpu = None
    energy = {key: 0.0 for key in ("cpu", "sensing", "communication", "actuation", "electronics", "cpu_switch")}
    sensor_count = control_count = switch_count = deadline_misses = 0
    max_error = error_sq = travelled_m = 0.0
    traces: list[dict] = []
    status = "timeout"
    steps = 0

    for step, event in enumerate(disturbance[:cfg.max_steps]):
        if physical.distance_to(cfg.path_m[-1]) <= cfg.goal_radius_m:
            status = "completed"
            break
        decision = select(policy, step, last_sensor, last_control,
                          event.complexity, cfg, previous_cpu)
        if not decision.feasible:
            status = "infeasible"
            break
        setting = decision.setting
        if previous_cpu is not None and setting.cpu_mode.name != previous_cpu:
            energy["cpu_switch"] += 0.004
            switch_count += 1
        previous_cpu = setting.cpu_mode.name

        # The estimator propagates with issued controls. A sensor reading corrects
        # the estimate but is not an oracle for the true pose.
        if decision.sensor_due:
            estimate = Pose(
                physical.x_m + event.measurement_x_m,
                physical.y_m + event.measurement_y_m,
                wrap_angle(physical.heading_rad + event.measurement_heading_rad),
            )
            sensor_count += 1
            last_sensor = step
            energy["sensing"] += 0.005
            energy["communication"] += 0.001
        energy["sensing"] += 0.04 * cfg.dt_s

        if decision.control_due:
            waypoint = _waypoint(estimate, waypoint, cfg)
            speed, turn = _controller(estimate, cfg.path_m[waypoint], cfg, setting.speed_factor)
            control_count += 1
            last_control = step

        if decision.execution_s > cfg.deadline_s + 1e-12:
            deadline_misses += 1
        energy["cpu"] += cpu_energy_j(decision.execution_s, setting.cpu_mode, cfg.dt_s)
        energy["electronics"] += 0.20 * cfg.dt_s
        energy["actuation"] += motor_power_w(speed, turn) * cfg.dt_s

        estimate = advance(estimate, speed, turn, cfg.dt_s)
        next_pose = advance(physical, speed * event.slip, turn + event.turn_noise_rps, cfg.dt_s)
        travelled_m += hypot(next_pose.x_m - physical.x_m, next_pose.y_m - physical.y_m)
        physical = next_pose
        tracking_error = cross_track_error(physical, cfg.path_m)
        error_sq += tracking_error ** 2
        max_error = max(max_error, tracking_error)
        steps = step + 1
        total_energy_j = sum(energy.values())
        battery_remaining_j = cfg.capacity_j - total_energy_j
        if record_trace:
            traces.append({
                "step": step, "time_s": round(steps * cfg.dt_s, 6),
                "x_m": round(physical.x_m, 6), "y_m": round(physical.y_m, 6),
                "heading_rad": round(physical.heading_rad, 6),
                "tracking_error_m": round(tracking_error, 6),
                "energy_total_j": round(total_energy_j, 6),
                "battery_remaining_j": round(battery_remaining_j, 6),
                "execution_s": round(decision.execution_s, 6),
                **setting.as_dict(),
            })
        if battery_remaining_j < cfg.reserve_j:
            status = "battery_reserve"
            break
        if tracking_error > cfg.tracking_error_limit_m:
            status = "tracking_limit"
            break
    else:
        if physical.distance_to(cfg.path_m[-1]) <= cfg.goal_radius_m:
            status = "completed"

    result = {
        "policy": policy,
        "seed": cfg.seed,
        "status": status,
        "completed": status == "completed",
        "steps": steps,
        "elapsed_s": round(steps * cfg.dt_s, 6),
        "energy_total_j": round(sum(energy.values()), 6),
        "energy_breakdown_j": {key: round(value, 6) for key, value in energy.items()},
        "battery_remaining_j": round(cfg.capacity_j - sum(energy.values()), 6),
        "distance_m": round(travelled_m, 6),
        "goal_distance_m": round(physical.distance_to(cfg.path_m[-1]), 6),
        "tracking_rms_m": round(sqrt(error_sq / steps), 6) if steps else None,
        "tracking_max_m": round(max_error, 6),
        "deadline_misses": deadline_misses,
        "sensor_samples": sensor_count,
        "control_updates": control_count,
        "cpu_switches": switch_count,
        # Energy per completed mission is undefined for failed missions.
        "energy_per_completed_mission_j": round(sum(energy.values()), 6) if status == "completed" else None,
    }
    if record_trace:
        result["trace"] = traces
    return result
