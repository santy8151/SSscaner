"""Versioned SAMPLE telemetry; measurements are fixtures, never OEM specifications."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator

ProtocolName = Literal["OBD-II", "CAN", "J1939", "EXTERNAL"]
Scenario = Literal[
    "normal",
    "low_refrigerant",
    "overcharge",
    "condenser_airflow",
    "fan_fault",
    "compressor_fault",
    "sensor_fault",
    "disconnected",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Reading(StrictModel):
    signal: Literal[
        "rpm",
        "engine_temperature",
        "voltage",
        "low_pressure",
        "high_pressure",
        "ambient_temperature",
        "evaporator_temperature",
        "compressor_on",
        "fan_on",
    ]
    value: FiniteFloat | None
    unit: Literal["rpm", "degC", "V", "psi_g", "bool"]
    quality: Literal["SAMPLE", "MISSING"] = "SAMPLE"

    @field_validator("unit")
    @classmethod
    def correct_unit(cls, unit, info):
        signal = info.data.get("signal")
        units = {
            "rpm": "rpm",
            "voltage": "V",
            "low_pressure": "psi_g",
            "high_pressure": "psi_g",
            "compressor_on": "bool",
            "fan_on": "bool",
        }
        if signal and unit != units.get(signal, "degC"):
            raise ValueError("Unidad incompatible con la señal")
        return unit


class TelemetryBatch(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    origin: Literal["SAMPLE"] = "SAMPLE"
    device_id: str = Field(min_length=1, max_length=100)
    protocol: ProtocolName
    sequence: int = Field(ge=0)
    observed_at: datetime
    idempotency_key: str = Field(min_length=1, max_length=100)
    readings: list[Reading] = Field(max_length=50)
    dtcs: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("observed_at")
    @classmethod
    def timezone_required(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamp debe incluir zona horaria")
        return value

    @field_validator("readings")
    @classmethod
    def unique_signals(cls, readings):
        if len({r.signal for r in readings}) != len(readings):
            raise ValueError("Señales duplicadas en el lote")
        for reading in readings:
            if (reading.value is None) != (reading.quality == "MISSING"):
                raise ValueError("Valor ausente requiere calidad MISSING y viceversa")
        return readings

    @field_validator("dtcs")
    @classmethod
    def sample_dtcs(cls, values):
        if any(not value.startswith("SAMPLE_") or len(value) > 80 for value in values):
            raise ValueError("Esta fase solo admite DTC SAMPLE explícitos")
        return values
