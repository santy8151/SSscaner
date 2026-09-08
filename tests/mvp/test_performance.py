import math

import pytest
from pydantic import ValidationError

from services.diagnosis.physics import PerformancePoint, PerformanceRequest, compare_performance


def point(**changes):
    return PerformancePoint(
        **{
            "torque_nm": 100,
            "shaft_rpm": 3000,
            "voltage_v": 400,
            "current_a": 100,
            "speed_kmh": 36,
            "turn_radius_m": 50,
            **changes,
        }
    )


def test_power_and_lateral_acceleration_are_descriptive_not_grip():
    result = compare_performance(
        PerformanceRequest(before=point(), after=point(torque_nm=110), conditions="SAMPLE controlled bench example")
    )
    assert result["before"]["shaft_power_kw"] == pytest.approx(10 * math.pi)
    assert result["before"]["steady_turn_acceleration_ms2"] == 2
    assert result["delta_shaft_power_kw"] == pytest.approx(math.pi)
    assert result["grip_improvement"] is None and result["ecu_commands"] is False


def test_impossible_energy_balance_does_not_fabricate_efficiency():
    result = compare_performance(
        PerformanceRequest(before=point(), after=point(current_a=1), conditions="SAMPLE inconsistent measurement")
    )
    assert result["after"]["apparent_efficiency"] is None
    assert result["after"]["energy_balance_consistent"] is False
    with pytest.raises(ValidationError):
        point(turn_radius_m=0)
    with pytest.raises(ValidationError):
        point(current_a=0)
