"""Explicit units and small, inspectable CPS component models."""
from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, pi, sin


def wrap_angle(angle: float) -> float:
    return (angle + pi) % (2 * pi) - pi


def clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class Pose:
    x_m: float = 0.0
    y_m: float = 0.0
    heading_rad: float = 0.0

    def distance_to(self, point: tuple[float, float]) -> float:
        return hypot(self.x_m - point[0], self.y_m - point[1])


def advance(pose: Pose, speed_mps: float, turn_rps: float, dt_s: float) -> Pose:
    midpoint = pose.heading_rad + 0.5 * turn_rps * dt_s
    return Pose(
        pose.x_m + speed_mps * cos(midpoint) * dt_s,
        pose.y_m + speed_mps * sin(midpoint) * dt_s,
        wrap_angle(pose.heading_rad + turn_rps * dt_s),
    )


def cross_track_error(pose: Pose, path: tuple[tuple[float, float], ...]) -> float:
    """Distance to closest piecewise-linear reference path segment, in metres."""
    error = float("inf")
    for (x0, y0), (x1, y1) in zip(path[:-1], path[1:]):
        dx, dy = x1 - x0, y1 - y0
        denom = dx * dx + dy * dy
        t = clip(((pose.x_m - x0) * dx + (pose.y_m - y0) * dy) / denom, 0.0, 1.0) if denom else 0.0
        error = min(error, hypot(pose.x_m - (x0 + t * dx), pose.y_m - (y0 + t * dy)))
    return error


@dataclass(frozen=True)
class CpuMode:
    name: str
    frequency_ghz: float
    active_w: float
    idle_w: float


CPU_MODES: tuple[CpuMode, ...] = (
    CpuMode("eco", 0.65, 0.80, 0.10),
    CpuMode("balanced", 1.20, 1.55, 0.16),
    CpuMode("performance", 1.80, 2.75, 0.22),
)


def cpu_execution_time_s(workload_gcycles: float, mode: CpuMode) -> float:
    # 1 giga-cycle / 1 GHz = 1 second.
    return workload_gcycles / mode.frequency_ghz


def cpu_energy_j(exec_s: float, mode: CpuMode, dt_s: float) -> float:
    # Overrun has its full active energy counted, even beyond the step boundary.
    return mode.active_w * exec_s + mode.idle_w * max(0.0, dt_s - exec_s)


def motor_power_w(speed_mps: float, turn_rps: float, *, active: bool = True) -> float:
    if not active:
        return 0.25
    return 3.5 + 9.0 * speed_mps**2 + 0.8 * turn_rps**2


@dataclass(frozen=True)
class Setting:
    sensor_period: int
    control_period: int
    cpu_mode: CpuMode
    speed_factor: float

    def as_dict(self) -> dict:
        return {
            "sensor_period": self.sensor_period,
            "control_period": self.control_period,
            "cpu_mode": self.cpu_mode.name,
            "speed_factor": self.speed_factor,
        }
