"""Decode explicitly configured numeric GATT packets, never infer vendor layouts."""

import math
import struct
from datetime import datetime
from typing import Literal

from pydantic import Field, FiniteFloat, field_validator

from packages.shared.contracts import StrictModel

UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


class BLEConfiguration(StrictModel):
    manufacturer: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    source_reference: str = Field(min_length=8, max_length=500)
    service_uuid: str = Field(pattern=UUID_PATTERN)
    characteristic_uuid: str = Field(pattern=UUID_PATTERN)
    signal: Literal["low_pressure", "high_pressure", "temperature", "voltage", "frequency"]
    unit: Literal["psi_g", "psi_abs", "kPa_g", "kPa_abs", "bar_g", "bar_abs", "degC", "V", "Hz"]
    encoding: Literal["uint8", "int16", "uint16", "int32", "uint32", "float32"]
    byte_order: Literal["little", "big"]
    byte_offset: int = Field(ge=0, le=508)
    scale: FiniteFloat = Field(gt=0, le=1000000)
    offset: FiniteFloat = Field(ge=-1000000, le=1000000)

    @field_validator("unit")
    @classmethod
    def appropriate_unit(cls, unit, info):
        signal = info.data.get("signal")
        if signal == "temperature" and unit != "degC":
            raise ValueError("Temperatura requiere degC")
        if signal == "voltage" and unit != "V":
            raise ValueError("Voltaje requiere V")
        if signal == "frequency" and unit != "Hz":
            raise ValueError("Frecuencia requiere Hz")
        if signal in {"low_pressure", "high_pressure"} and unit in {"degC", "V", "Hz"}:
            raise ValueError("Presión requiere unidad y referencia de presión")
        return unit


class DeviceCreate(StrictModel):
    name: str = Field(min_length=1, max_length=150)
    vehicle_id: str = Field(min_length=1, max_length=36)
    configuration: BLEConfiguration


class BLEPacket(StrictModel):
    origin: Literal["CLIENT_BLE"]
    raw_hex: str = Field(min_length=2, max_length=1024, pattern=r"^(?:[0-9a-fA-F]{2})+$")
    observed_at: datetime
    idempotency_key: str = Field(min_length=1, max_length=100)

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamp requiere zona horaria")
        return value


def decode_packet(configuration: BLEConfiguration, raw_hex: str) -> float:
    formats = {"uint8": "B", "int16": "h", "uint16": "H", "int32": "i", "uint32": "I", "float32": "f"}
    payload = bytes.fromhex(raw_hex)
    layout = ("<" if configuration.byte_order == "little" else ">") + formats[configuration.encoding]
    if len(payload) < configuration.byte_offset + struct.calcsize(layout):
        raise ValueError("Trama demasiado corta para la configuración declarada")
    raw_value = struct.unpack_from(layout, payload, configuration.byte_offset)[0]
    value = raw_value * configuration.scale + configuration.offset
    if not math.isfinite(value):
        raise ValueError("El dispositivo entregó un valor no finito")
    return value
