from math import isclose, pi

from eco_cps.model import CPU_MODES, Pose, advance, cpu_energy_j, cpu_execution_time_s, cross_track_error, wrap_angle
from eco_cps.policy import workload_gcycles


def test_units_and_energy_accounting():
    eco = CPU_MODES[0]
    runtime = cpu_execution_time_s(0.065, eco)
    assert isclose(runtime, 0.1)
    assert isclose(cpu_energy_j(runtime, eco, 0.1), 0.08)
    assert cpu_energy_j(0.15, eco, 0.1) > 0.08
    assert workload_gcycles(sensor_due=True, control_due=True, complexity=1.0) == 0.072


def test_geometry_and_pose_propagation():
    pose = advance(Pose(), 1.0, 0.0, 1.0)
    assert isclose(pose.x_m, 1.0)
    assert isclose(pose.y_m, 0.0)
    assert isclose(cross_track_error(Pose(0.5, 1.0), ((0.0, 0.0), (1.0, 0.0))), 1.0)
    assert isclose(wrap_angle(3.0 * pi), -pi)
