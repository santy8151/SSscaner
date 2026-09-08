import pytest
from pydantic import ValidationError

from hardware.simulator.vehicle import VehicleSimulator
from packages.protocols.interfaces import MachineIntegration
from packages.shared.contracts import TelemetryBatch


@pytest.mark.parametrize("change", ["nan", "timezone", "origin", "dtc", "duplicate", "quality"])
def test_invalid_telemetry(change):
    payload = VehicleSimulator().read_sample(0).model_dump(mode="json")
    if change == "nan":
        payload["readings"][0]["value"] = float("nan")
    elif change == "timezone":
        payload["observed_at"] = "2026-09-07T10:00:00"
    elif change == "origin":
        payload["origin"] = "HARDWARE"
    elif change == "dtc":
        payload["dtcs"] = ["INVENTED_OEM_CODE"]
    elif change == "duplicate":
        payload["readings"].append(payload["readings"][0])
    else:
        payload["readings"][0]["value"] = None
    with pytest.raises(ValidationError):
        TelemetryBatch.model_validate(payload)


def test_no_machine_control_and_no_real_protocol_claim():
    assert MachineIntegration().capabilities()["physical_control"] is False
    assert not hasattr(MachineIntegration(), "execute")
    assert VehicleSimulator().capabilities()["wire_protocol_emulation"] is False
