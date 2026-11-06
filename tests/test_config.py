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
