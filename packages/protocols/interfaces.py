"""Read-only hardware abstraction. No physical write/control API exists."""

from typing import Protocol

from packages.shared.contracts import TelemetryBatch


class HardwareAdapter(Protocol):
    def capabilities(self) -> dict: ...
    def read_sample(self, sequence: int) -> TelemetryBatch: ...
    def close(self) -> None: ...


class MachineIntegration:
    """Reserved boundary: no station protocol is assumed or implemented."""

    def capabilities(self) -> dict:
        return {"enabled": False, "status": "SOURCE_REQUIRED", "physical_control": False}
