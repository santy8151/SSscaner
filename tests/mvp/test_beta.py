import struct
import time

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from apps.api.main import create_app
from hardware.ble import BLEConfiguration, decode_packet
from services.ml.lab import TrainingRequest, train_sample
from tests.mvp.test_api import register, vehicle

# Explicitly fictitious UUIDs and conversion for automated tests only.
CONFIG = {
    "manufacturer": "TEST",
    "model": "FIXTURE",
    "source_reference": "TEST_FIXTURE_NOT_OEM",
    "service_uuid": "11111111-1111-1111-1111-111111111111",
    "characteristic_uuid": "22222222-2222-2222-2222-222222222222",
    "signal": "low_pressure",
    "unit": "psi_g",
    "encoding": "uint16",
    "byte_order": "little",
    "byte_offset": 0,
    "scale": 0.1,
    "offset": 0,
}


@pytest.fixture
def client(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'beta.db'}", "test", rate_limit=10000)
    app.state.training_runner.artifact_dir = tmp_path / "models"
    with TestClient(app) as client:
        yield client


def test_ble_decode_requires_explicit_layout_and_preserves_pressure_reference():
    config = BLEConfiguration(**CONFIG)
    assert decode_packet(config, "5e01") == 35
    with pytest.raises(ValueError, match="corta"):
        decode_packet(config, "01")
    with pytest.raises(ValidationError):
        BLEConfiguration(**{**CONFIG, "unit": "V"})
    float_config = BLEConfiguration(**{**CONFIG, "encoding": "float32"})
    with pytest.raises(ValueError, match="finito"):
        decode_packet(float_config, struct.pack("<f", float("nan")).hex())
    big_endian = BLEConfiguration(**{**CONFIG, "byte_order": "big", "unit": "psi_abs"})
    assert decode_packet(big_endian, "015e") == 35
    assert big_endian.unit == "psi_abs"


def test_ble_packet_persistence_idempotence_and_tenant_isolation(client):
    headers = register(client)
    asset = vehicle(client, headers)
    created = client.post(
        "/api/v1/devices", headers=headers, json={"name": "TEST gauge", "vehicle_id": asset, "configuration": CONFIG}
    )
    assert created.status_code == 201, created.text
    profile_id = created.json()["id"]
    assert created.json()["validation_status"] == "UNVERIFIED_MAPPING"
    packet = {
        "origin": "CLIENT_BLE",
        "raw_hex": "5e01",
        "observed_at": "2026-09-07T12:00:00Z",
        "idempotency_key": "test-packet-1",
    }
    endpoint = f"/api/v1/devices/{profile_id}/readings"
    response = client.post(endpoint, headers=headers, json=packet)
    assert response.status_code == 200, response.text
    assert response.json()["value"] == 35
    assert response.json()["provenance"] == "browser_reported_not_device_attested"
    assert client.post(endpoint, headers=headers, json=packet).json()["status"] == "duplicate"
    assert client.post(endpoint, headers=headers, json={**packet, "raw_hex": "0000"}).status_code == 409
    assert client.post(endpoint, headers=headers, json={**packet, "origin": "SAMPLE"}).status_code == 422
    other = register(client, "other-company")
    assert client.get(endpoint, headers=other).status_code == 404
    assert client.post(endpoint, headers=other, json=packet).status_code == 404
    assert client.get("/api/v1/devices", headers=other).json() == []
    assert client.get("/api/v1/beta/status", headers=headers).json()["browser_ble_packets"] == 1


@pytest.mark.parametrize(
    "configuration",
    [
        {"model": "mlp", "epochs": 3, "batch_size": 16, "hidden_layers": [8], "learning_rate": 0.001},
        {"model": "random_forest", "trees": 10, "max_depth": 3},
    ],
)
def test_real_sample_training_saves_artifact_and_measures_metrics(tmp_path, configuration):
    request = TrainingRequest(dataset_origin="SAMPLE", configuration=configuration, samples_per_class=25, seed=7)
    artifact = tmp_path / "model.joblib"
    progress = []
    result = train_sample(request, progress.append, artifact)
    assert artifact.is_file() and artifact.stat().st_size > 100
    assert result["training_samples"] + result["test_samples"] == 175
    assert 0 <= result["accuracy_sample"] <= 1
    assert len(result["confusion_matrix"]) == 7
    assert result["valid_for_real_diagnosis"] is False
    assert result["calibration_authority"] is False
    assert len(result["dataset_hash"]) == 64
    if configuration["model"] == "mlp":
        assert len(result["loss_curve"]) == 3


def test_training_job_and_restricted_inputs(client):
    headers = register(client)
    body = {
        "dataset_origin": "SAMPLE",
        "configuration": {"model": "mlp", "epochs": 2, "batch_size": 16, "hidden_layers": [8]},
        "samples_per_class": 25,
    }
    bad = {**body, "dataset_origin": "REAL"}
    assert client.post("/api/v1/ml/runs", headers=headers, json=bad).status_code == 422
    bad = {**body, "configuration": {"model": "mlp", "learning_rate": 100}}
    assert client.post("/api/v1/ml/runs", headers=headers, json=bad).status_code == 422
    response = client.post("/api/v1/ml/runs", headers=headers, json=body)
    assert response.status_code == 202, response.text
    run_id = response.json()["id"]
    result = {}
    for _ in range(60):
        result = client.get(f"/api/v1/ml/runs/{run_id}", headers=headers).json()
        if result["status"] in {"completed", "failed"}:
            break
        time.sleep(0.05)
    assert result["status"] == "completed", result
    assert result["progress"] == 100
    other = register(client, "other-company")
    assert client.get(f"/api/v1/ml/runs/{run_id}", headers=other).status_code == 404
    assert client.get("/api/v1/ml/runs", headers=other).json() == []
