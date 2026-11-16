"""Reject malformed and non-finite experiment configurations before simulation."""
from dataclasses import replace
import math

import pytest

from eco_cps.config import ExperimentConfig, load_config


@pytest.mark.parametrize("field,value", [
    ("dt_s", math.nan), ("capacity_j", math.inf),
    ("sensor_noise_m", -math.inf), ("reserve_j", math.nan),
    ("deadline_s", True),
])
def test_nonfinite_or_boolean_scalar_parameters_rejected(field, value):
    with pytest.raises(ValueError, match=field):
        replace(ExperimentConfig(), **{field: value}).validated()


@pytest.mark.parametrize("field,value", [
    ("seed", True), ("seed", 1.5),
    ("max_steps", 2.5), ("max_sensor_age_steps", False),
    ("max_control_age_steps", 2.0),
])
def test_integer_only_parameters_rejected(field, value):
    with pytest.raises(ValueError, match=field):
        replace(ExperimentConfig(), **{field: value}).validated()


@pytest.mark.parametrize("path", [
    ((0.0, 0.0), (math.nan, 1.0)),
    ((0.0, 0.0), (math.inf, 1.0)),
    ((0.0, 0.0), ("x", 1.0)),
    ((0.0, 0.0), (True, 1.0)),
    ((0.0, 0.0), 1),
])
def test_invalid_waypoints_rejected(path):
    with pytest.raises(ValueError, match="path_m"):
        replace(ExperimentConfig(), path_m=path).validated()


def test_malformed_waypoint_json_rejected(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"path_m": [null, [1, 2]]}')
    with pytest.raises(ValueError, match="path_m"):
        load_config(path)
