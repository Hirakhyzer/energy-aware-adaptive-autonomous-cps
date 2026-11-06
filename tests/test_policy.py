from dataclasses import replace

from eco_cps.config import ExperimentConfig
from eco_cps.model import CPU_MODES
from eco_cps.policy import POLICY_NAMES, candidates, select


def test_policy_ablation_spaces_are_distinct():
    assert set(POLICY_NAMES) == {"fixed", "sensing_only", "compute_only", "control_only", "joint"}
    assert len(candidates("fixed")) == 1
    assert len(candidates("sensing_only")) == 3
    assert len(candidates("compute_only")) == 3
    assert len(candidates("control_only")) == 9
    assert len(candidates("joint")) == 81


def test_joint_decision_respects_deadlines():
    cfg = ExperimentConfig().validated()
    for step in range(1, 21):
        decision = select("joint", step, step - 2, step - 3, 1.45, cfg, "eco")
        assert decision.feasible
        assert decision.execution_s <= cfg.deadline_s


def test_no_feasible_solution_is_reported_not_claimed_safe():
    cfg = replace(ExperimentConfig(), deadline_s=0.001).validated()
    decision = select("joint", 0, -1000, -1000, 1.0, cfg, None)
    assert not decision.feasible
    assert decision.reason == "deadline"
