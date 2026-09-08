"""Fail-closed calibration boundary. Deliberately independent of AI/telemetry."""


def evaluate(vehicle_id: str) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "status": "SOURCE_REQUIRED",
        "profile_id": None,
        "version": None,
        "refrigerant": None,
        "charge_grams": None,
        "oil_type": None,
        "oil_quantity_ml": None,
        "vacuum_time_minutes": None,
        "validation_method": "blocked_missing_approved_source",
        "physical_control": False,
        "missing": [
            "Identificación exacta del sistema A/C",
            "Ficha OEM aprobada y versionada",
            "Aplicabilidad del refrigerante y aceite",
            "Tolerancias y procedimiento oficial",
        ],
        "message": "No hay especificación aprobada. No se genera perfil ni se calcula carga a partir de presiones.",
    }
