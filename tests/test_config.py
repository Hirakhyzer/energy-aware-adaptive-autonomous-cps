from dataclasses import replace
import json

import pytest

from eco_cps.config import ExperimentConfig, load_config


def test_valid_default_and_json_override(tmp_path):
    defaults = ExperimentConfig().validated()
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"seed": 23, "path_m": [[0, 0], [1, 2]]}))
    config = load_config(path)
    assert config.seed == 23
    assert config.path_m == ((0, 0), (1, 2))
    assert defaults.max_steps > 0


@pytest.mark.parametrize("changes", [
    {"dt_s": 0.0}, {"max_steps": 0}, {"sensor_noise_m": -0.2},
    {"reserve_j": 4000.0}, {"path_m": ((0, 0),)},
    {"path_m": ((0, 0), (0, 0))}, {"seed": -1},
])
def test_invalid_parameters_rejected(changes):
    with pytest.raises(ValueError):
        replace(ExperimentConfig(), **changes).validated()


def test_unknown_config_key_rejected(tmp_path):
    config = tmp_path / "bad.json"
    config.write_text('{"unknown": true}')
    with pytest.raises(ValueError, match="unknown config keys"):
        load_config(config)


@pytest.mark.parametrize(("field", "value"), [
    ("dt_s", float("nan")),
    ("max_speed_mps", float("inf")),
    ("reserve_j", float("-inf")),
    ("sensor_noise_m", "0.02"),
    ("heading_noise_rad", True),
    ("max_steps", 2.5),
    ("max_sensor_age_steps", True),
    ("max_control_age_steps", 1.1),
    ("seed", 2.4),
    ("seed", True),
])
def test_invalid_numeric_types_and_nonfinite_values_rejected(field, value):
    with pytest.raises(ValueError, match=field):
        replace(ExperimentConfig(), **{field: value}).validated()


@pytest.mark.parametrize("route", [
    None,
    "not a route",
    ((0, 0), 42),
    ((0, 0), ("1", 2)),
    ((0, 0), (float("nan"), 2)),
    ((0, 0), (float("inf"), 2)),
    ((0, 0), (True, 2)),
])
def test_malformed_route_rejected_with_value_error(route):
    with pytest.raises(ValueError, match="path_m"):
        replace(ExperimentConfig(), path_m=route).validated()


@pytest.mark.parametrize("payload", [
    {"path_m": None},
    {"path_m": "invalid"},
    {"path_m": [[0, 0], 5]},
    {"path_m": [[0, 0], [float("nan"), 2]]},
    {"max_steps": 5.5},
    {"seed": True},
])
def test_json_configuration_errors_are_value_errors(tmp_path, payload):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)
