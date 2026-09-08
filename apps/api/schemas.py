import re
from typing import Literal

from pydantic import Field, field_validator

from packages.shared.contracts import ProtocolName, Scenario, StrictModel


class Credentials(StrictModel):
    organization: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]+[a-z0-9]$")
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def email_valid(cls, value):
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Email inválido")
        return value.lower()


class MemberCreate(StrictModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    role: Literal["admin", "technician", "viewer"]

    _email_valid = field_validator("email")(Credentials.email_valid.__func__)


class VehicleCreate(StrictModel):
    name: str = Field(min_length=1, max_length=150)
    kind: Literal["light", "heavy", "machinery"] = "light"
    manufacturer: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    year: int | None = Field(default=None, ge=1900, le=2100)


class SimulationCreate(StrictModel):
    vehicle_id: str = Field(min_length=1, max_length=36)
    scenario: Scenario = "normal"
    protocol: ProtocolName = "J1939"


class DiagnosticCreate(StrictModel):
    scan_id: str = Field(min_length=1, max_length=36)


class CalibrationEvaluate(StrictModel):
    vehicle_id: str = Field(min_length=1, max_length=36)
