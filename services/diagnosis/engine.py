from packages.shared.contracts import TelemetryBatch


def evaluate(batch: TelemetryBatch) -> dict:
    missing = [reading.signal for reading in batch.readings if reading.quality == "MISSING"]
    return {
        "status": "SOURCE_REQUIRED",
        "engine_version": "contract-0.1",
        "origin": batch.origin,
        "confidence": None,
        "hypotheses": [],
        "evidence": {"available_signals": len(batch.readings), "missing_signals": missing, "dtcs": batch.dtcs},
        "recommendations": [
            "Datos SAMPLE: no representan un vehículo real.",
            "Se requieren reglas técnicas revisadas y referencias aplicables para emitir hipótesis de avería.",
        ],
    }
