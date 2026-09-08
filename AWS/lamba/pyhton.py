import json
import os
from urllib import request, error


def lambda_handler(event, context):
    """Procesa un evento de diagnóstico para enviar mediciones al backend de SSSCANER."""
    try:
        payload = event if isinstance(event, dict) else json.loads(event)
        api_url = os.getenv("SSSCANER_API_URL", "http://localhost:8000/api/v1/ml/diagnose")
        vehicle_id = payload.get("vehicle_id", "VH001")
        measurements = payload.get("measurements", {
            "pressure_suction": 28,
            "pressure_discharge": 245,
            "temperature_evaporator": 6,
            "temperature_condenser": 47,
            "voltage": 12.1,
            "current": 5.3,
        })

        body = json.dumps({
            "vehicle_id": vehicle_id,
            "measurements": measurements,
        }).encode("utf-8")

        req = request.Request(
            api_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        with request.urlopen(req, timeout=10) as response:
            response_body = response.read().decode("utf-8")
            data = json.loads(response_body)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Diagnóstico enviado correctamente",
                "vehicle_id": vehicle_id,
                "payload": data,
            }),
        }
    except error.URLError as exc:
        return {
            "statusCode": 503,
            "body": json.dumps({
                "message": "No se pudo contactar el backend",
                "detail": str(exc),
            }),
        }
    except Exception as exc:  # pragma: no cover
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Error inesperado en Lambda",
                "detail": str(exc),
            }),
        }


if __name__ == "__main__":
    print(lambda_handler({"vehicle_id": "VH001"}, None))
