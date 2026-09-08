"""Deterministic UI fixtures, not technical service limits or CAN frames."""

import math
from datetime import datetime, timezone
from typing import get_args

from packages.shared.contracts import ProtocolName, Reading, Scenario, TelemetryBatch

SCENARIOS = list(get_args(Scenario))


class VehicleSimulator:
    def __init__(self, scenario: Scenario = "normal", protocol: ProtocolName = "J1939"):
        if scenario not in SCENARIOS or protocol not in get_args(ProtocolName):
            raise ValueError("Escenario o protocolo no soportado")
        self.scenario = scenario
        self.protocol = protocol

    def capabilities(self) -> dict:
        return {
            "origin": "SAMPLE",
            "physical_connection": False,
            "wire_protocol_emulation": False,
            "scenarios": SCENARIOS,
        }

    def read_sample(self, sequence: int) -> TelemetryBatch:
        values = {
            "rpm": (1500 + round(20 * math.sin(sequence)), "rpm"),
            "engine_temperature": (85, "degC"),
            "voltage": (13.8, "V"),
            "low_pressure": (35, "psi_g"),
            "high_pressure": (210, "psi_g"),
            "ambient_temperature": (30, "degC"),
            "evaporator_temperature": (8, "degC"),
            "compressor_on": (1, "bool"),
            "fan_on": (1, "bool"),
        }
        changes = {
            "low_refrigerant": {"low_pressure": 18, "high_pressure": 145},
            "overcharge": {"low_pressure": 55, "high_pressure": 310},
            "condenser_airflow": {"high_pressure": 300, "evaporator_temperature": 16},
            "fan_fault": {"fan_on": 0, "high_pressure": 300},
            "compressor_fault": {"compressor_on": 0, "low_pressure": 80, "high_pressure": 90},
            "sensor_fault": {"low_pressure": None},
        }
        for key, value in changes.get(self.scenario, {}).items():
            values[key] = (value, values[key][1])
        readings = (
            []
            if self.scenario == "disconnected"
            else [
                Reading(signal=key, value=value, unit=unit, quality="MISSING" if value is None else "SAMPLE")
                for key, (value, unit) in values.items()
            ]
        )
        return TelemetryBatch(
            device_id="SAMPLE-SSSCANNER-01",
            protocol=self.protocol,
            sequence=sequence,
            observed_at=datetime.now(timezone.utc),
            idempotency_key=f"sample-{sequence}",
            readings=readings,
            dtcs=["SAMPLE_SENSOR_FAULT"] if self.scenario == "sensor_fault" else [],
        )

    def close(self) -> None:
        return None
