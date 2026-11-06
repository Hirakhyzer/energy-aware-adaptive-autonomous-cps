"""Enumerative energy-aware policy with explicit feasibility filters."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import inf

from .config import ExperimentConfig
from .model import CPU_MODES, Setting, cpu_energy_j, cpu_execution_time_s, motor_power_w

POLICY_NAMES = ("fixed", "sensing_only", "compute_only", "control_only", "joint")
PERFORMANCE = CPU_MODES[-1]
FIXED = Setting(1, 1, PERFORMANCE, 1.0)


@dataclass(frozen=True)
class Decision:
    setting: Setting
    sensor_due: bool
    control_due: bool
    execution_s: float
    feasible: bool
    reason: str


def workload_gcycles(*, sensor_due: bool, control_due: bool, complexity: float) -> float:
    return complexity * (0.022 + (0.018 if sensor_due else 0.0) + (0.032 if control_due else 0.0))


def predicted_uncertainty_m(age_steps: int, speed_mps: float, cfg: ExperimentConfig) -> float:
    # Transparent heuristic proxy; not a probabilistic confidence bound.
    return cfg.sensor_noise_m + 0.11 * speed_mps * age_steps * cfg.dt_s


def candidates(policy: str) -> tuple[Setting, ...]:
    if policy not in POLICY_NAMES:
        raise ValueError(f"unknown policy {policy!r}; available: {', '.join(POLICY_NAMES)}")
    if policy == "fixed":
        return (FIXED,)
    sensor_periods = (1, 2, 4) if policy in ("sensing_only", "joint") else (1,)
    control_periods = (1, 2, 4) if policy in ("control_only", "joint") else (1,)
    modes = CPU_MODES if policy in ("compute_only", "joint") else (PERFORMANCE,)
    speeds = (0.70, 0.85, 1.0) if policy in ("control_only", "joint") else (1.0,)
    return tuple(Setting(s, c, m, v) for s, c, m, v in product(sensor_periods, control_periods, modes, speeds))


def _decision(setting: Setting, step: int, last_sensor: int, last_control: int,
              complexity: float, cfg: ExperimentConfig) -> Decision:
    sensor_age = step - last_sensor
    control_age = step - last_control
    sensor_due = sensor_age >= setting.sensor_period
    control_due = control_age >= setting.control_period
    execution = cpu_execution_time_s(workload_gcycles(sensor_due=sensor_due,
                                          control_due=control_due, complexity=complexity), setting.cpu_mode)
    reason = "ok"
    if execution > min(cfg.deadline_s, cfg.dt_s) + 1e-12:
        reason = "deadline"
    elif not sensor_due and sensor_age > cfg.max_sensor_age_steps:
        reason = "sensor age"
    elif not control_due and control_age > cfg.max_control_age_steps:
        reason = "control age"
    elif predicted_uncertainty_m(0 if sensor_due else sensor_age,
            cfg.max_speed_mps * setting.speed_factor, cfg) > cfg.predicted_uncertainty_limit_m:
        reason = "uncertainty proxy"
    return Decision(setting, sensor_due, control_due, execution, reason == "ok", reason)


def select(policy: str, step: int, last_sensor: int, last_control: int,
           complexity: float, cfg: ExperimentConfig, previous_cpu: str | None) -> Decision:
    """Minimize approximate energy per forward metre among currently feasible settings.

    This is a one-step heuristic, NOT an optimal solution to the full mission.
    """
    options = [_decision(s, step, last_sensor, last_control, complexity, cfg) for s in candidates(policy)]
    feasible = [d for d in options if d.feasible]
    if not feasible:
        # No silently asserted feasibility: record the reason at the call site.
        return _decision(FIXED, step, last_sensor, last_control, complexity, cfg)
    if policy == "fixed":
        return feasible[0]

    def score(decision: Decision) -> tuple[float, int, int, str]:
        s = decision.setting
        dt = cfg.dt_s
        speed = cfg.max_speed_mps * s.speed_factor
        # Average duty cycling and workload across configured periods.
        average_cycles = complexity * (0.022 + 0.018 / s.sensor_period + 0.032 / s.control_period)
        cpu_s = cpu_execution_time_s(average_cycles, s.cpu_mode)
        cpu_j = cpu_energy_j(cpu_s, s.cpu_mode, dt)
        sensor_j = 0.04 * dt + 0.005 / s.sensor_period
        radio_j = 0.001 / s.sensor_period
        motor_j = motor_power_w(speed, 0.12) * dt
        misc_j = 0.20 * dt
        switch_j = 0.004 if previous_cpu is not None and previous_cpu != s.cpu_mode.name else 0.0
        predicted_energy_per_m = (cpu_j + sensor_j + radio_j + motor_j + misc_j + switch_j) / max(speed * dt, 1e-6)
        control_penalty = 0.08 * (s.control_period - 1) + 0.05 * (s.sensor_period - 1)
        return (predicted_energy_per_m + control_penalty, s.sensor_period, s.control_period, s.cpu_mode.name)

    return min(feasible, key=score)
