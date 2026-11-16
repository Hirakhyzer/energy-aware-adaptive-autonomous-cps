"""Strict JSON experiment configuration with reproducible defaults."""
from __future__ import annotations

from dataclasses import dataclass, fields, replace
import json
import math
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExperimentConfig:
    dt_s: float = 0.1
    max_steps: int = 250
    seed: int = 7
    path_m: tuple[tuple[float, float], ...] = ((0.0, 0.0), (2.4, 0.0), (3.7, 1.1), (5.8, 1.1))
    goal_radius_m: float = 0.24
    max_speed_mps: float = 0.8
    max_turn_rps: float = 1.5
    sensor_noise_m: float = 0.025
    heading_noise_rad: float = 0.015
    slip_sigma: float = 0.035
    turn_noise_rps: float = 0.035
    deadline_s: float = 0.085
    tracking_error_limit_m: float = 0.90
    predicted_uncertainty_limit_m: float = 0.18
    max_sensor_age_steps: int = 4
    max_control_age_steps: int = 4
    capacity_j: float = 3600.0
    reserve_j: float = 100.0

    def validated(self) -> ExperimentConfig:
        for key in ("max_steps", "max_sensor_age_steps", "max_control_age_steps", "seed"):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{key} must be an integer")
        positive = (
            "dt_s", "max_steps", "goal_radius_m", "max_speed_mps", "max_turn_rps",
            "deadline_s", "tracking_error_limit_m", "predicted_uncertainty_limit_m",
            "max_sensor_age_steps", "max_control_age_steps", "capacity_j",
        )
        for key in positive:
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{key} must be finite and numeric")
            if getattr(self, key) <= 0:
                raise ValueError(f"{key} must be > 0")
        for key in ("sensor_noise_m", "heading_noise_rad", "slip_sigma", "turn_noise_rps", "reserve_j"):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{key} must be finite and numeric")
            if getattr(self, key) < 0:
                raise ValueError(f"{key} must be >= 0")
        if self.reserve_j >= self.capacity_j:
            raise ValueError("reserve_j must be smaller than capacity_j")
        if not isinstance(self.path_m, (list, tuple)) or len(self.path_m) < 2 or any(
            not isinstance(point, (list, tuple)) or len(point) != 2 for point in self.path_m
        ):
            raise ValueError("path_m must contain at least two x,y points")
        if any(
            isinstance(coord, bool) or not isinstance(coord, (int, float)) or not math.isfinite(coord)
            for point in self.path_m for coord in point
        ):
            raise ValueError("path_m coordinates must be finite numbers")
        if all(point == self.path_m[0] for point in self.path_m):
            raise ValueError("path_m must contain a nonzero-length segment")
        if self.seed < 0:
            raise ValueError("seed must be nonnegative")
        return self

    def as_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


def load_config(path: str | Path | None = None, *, seed: int | None = None) -> ExperimentConfig:
    cfg = ExperimentConfig()
    if path is not None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("configuration must be a JSON object")
        allowed = {f.name for f in fields(cfg)}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"unknown config keys: {', '.join(sorted(unknown))}")
        if "path_m" in data:
            raw_path = data["path_m"]
            if not isinstance(raw_path, (list, tuple)) or any(
                not isinstance(point, (list, tuple)) for point in raw_path
            ):
                raise ValueError("path_m must be an array of x,y points")
            data["path_m"] = tuple(tuple(point) for point in raw_path)
        cfg = replace(cfg, **data)
    if seed is not None:
        cfg = replace(cfg, seed=seed)
    return cfg.validated()
