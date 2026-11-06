from dataclasses import replace

import pytest

from eco_cps.config import ExperimentConfig
from eco_cps.policy import POLICY_NAMES
from eco_cps.simulation import simulate


@pytest.mark.parametrize("policy", POLICY_NAMES)
def test_nominal_mission_completes_with_constraints(policy):
    result = simulate(policy, ExperimentConfig(seed=7))
    assert result["status"] == "completed"
    assert result["deadline_misses"] == 0
    assert result["tracking_max_m"] <= 0.9
    assert 0 < result["energy_total_j"] < 3600.0
    assert result["battery_remaining_j"] > 100.0
    assert abs(sum(result["energy_breakdown_j"].values()) - result["energy_total_j"]) < 0.00001


def test_same_seed_gives_identical_results_and_traces():
    cfg = ExperimentConfig(seed=17)
    assert simulate("joint", cfg, record_trace=True) == simulate("joint", cfg, record_trace=True)


def test_trace_has_consistent_timestamps_and_energy():
    result = simulate("joint", ExperimentConfig(seed=7), record_trace=True)
    assert result["steps"] == len(result["trace"])
    assert result["trace"][-1]["energy_total_j"] == result["energy_total_j"]
    assert all(a["energy_total_j"] <= b["energy_total_j"]
               for a, b in zip(result["trace"][:-1], result["trace"][1:]))


def test_unachievable_deadline_is_not_silently_accepted():
    cfg = replace(ExperimentConfig(), deadline_s=0.001)
    result = simulate("joint", cfg)
    assert result["status"] == "infeasible"
    assert not result["completed"]
    assert result["energy_per_completed_mission_j"] is None


def test_battery_reserve_stop_is_explicit():
    cfg = replace(ExperimentConfig(), capacity_j=101.0, reserve_j=100.0)
    result = simulate("fixed", cfg)
    assert result["status"] == "battery_reserve"
    assert not result["completed"]
