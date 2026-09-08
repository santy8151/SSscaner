import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.database import AuthSession, User
from apps.api.main import create_app
from hardware.simulator.vehicle import SCENARIOS, VehicleSimulator

PASSWORD = "Test-only-long-password!"


@pytest.fixture
def client(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'test.db'}", environment="test", rate_limit=10000)
    with TestClient(app) as client:
        yield client


def register(client, organization="test-workshop"):
    response = client.post(
        "/api/v1/auth/register",
        json={"organization": organization, "email": "admin@example.test", "password": PASSWORD},
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def vehicle(client, headers):
    response = client.post("/api/v1/vehicles", headers=headers, json={"name": "SAMPLE Excavator", "kind": "machinery"})
    assert response.status_code == 201
    return response.json()["id"]


def scan(client, headers, vehicle_id):
    response = client.post(
        "/api/v1/simulator/scans",
        headers=headers,
        json={"vehicle_id": vehicle_id, "scenario": "normal", "protocol": "J1939"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_health_and_database(client):
    assert client.get("/health").json()["hardware"] == "SAMPLE_AND_CLIENT_BLE"
    assert client.get("/ready").json()["status"] == "ready"


def test_auth_hashing_logout_and_expiry(client):
    headers = register(client)
    assert client.get("/api/v1/me", headers=headers).json()["role"] == "admin"
    with client.app.state.session_factory() as db:
        user = db.scalar(select(User))
        assert user.password_hash != PASSWORD
        assert user.password_hash.startswith("scrypt$")
        session = db.scalar(select(AuthSession))
        assert session.token_hash not in headers["Authorization"]
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/v1/me", headers=headers).status_code == 401
    login = client.post(
        "/api/v1/auth/login",
        json={"organization": "test-workshop", "email": "admin@example.test", "password": PASSWORD},
    )
    assert login.status_code == 200
    with client.app.state.session_factory() as db:
        session = db.scalar(select(AuthSession))
        session.expires_at = time.time() - 1
        db.commit()
    assert (
        client.get("/api/v1/me", headers={"Authorization": "Bearer " + login.json()["access_token"]}).status_code == 401
    )


def test_unauthorized_and_cross_tenant_access(client):
    assert client.get("/api/v1/vehicles").status_code == 401
    first = register(client, "workshop-one")
    second = register(client, "workshop-two")
    asset = vehicle(client, first)
    capture = scan(client, first, asset)
    assert client.get("/api/v1/vehicles", headers=second).json() == []
    assert client.get(f"/api/v1/scans/{capture['id']}", headers=second).status_code == 404
    assert client.post("/api/v1/calibration/evaluate", headers=second, json={"vehicle_id": asset}).status_code == 404
    assert client.post("/api/v1/simulator/scans", headers=second, json={"vehicle_id": asset}).status_code == 404
    assert client.post("/api/v1/diagnostics", headers=second, json={"scan_id": capture["id"]}).status_code == 404


def test_rbac_viewer_cannot_write_or_create_admin(client):
    headers = register(client)
    response = client.post(
        "/api/v1/members",
        headers=headers,
        json={"email": "viewer@example.test", "password": PASSWORD, "role": "viewer"},
    )
    assert response.status_code == 201, response.text
    login = client.post(
        "/api/v1/auth/login",
        json={"organization": "test-workshop", "email": "viewer@example.test", "password": PASSWORD},
    )
    viewer = {"Authorization": "Bearer " + login.json()["access_token"]}
    assert client.get("/api/v1/vehicles", headers=viewer).status_code == 200
    assert client.post("/api/v1/vehicles", headers=viewer, json={"name": "No"}).status_code == 403
    assert (
        client.post(
            "/api/v1/members", headers=viewer, json={"email": "new@example.test", "password": PASSWORD, "role": "admin"}
        ).status_code
        == 403
    )
    assert client.get("/api/v1/audit", headers=viewer).status_code == 403


def test_calibration_fails_closed_and_diagnosis_has_no_fake_confidence(client):
    headers = register(client)
    asset = vehicle(client, headers)
    capture = scan(client, headers, asset)
    diagnosis = client.post("/api/v1/diagnostics", headers=headers, json={"scan_id": capture["id"]}).json()
    assert diagnosis["confidence"] is None
    assert diagnosis["hypotheses"] == []
    calibration = client.post("/api/v1/calibration/evaluate", headers=headers, json={"vehicle_id": asset}).json()
    assert calibration["status"] == "SOURCE_REQUIRED"
    assert calibration["charge_grams"] is None
    assert calibration["physical_control"] is False
    assert (
        client.post(
            "/api/v1/calibration/evaluate",
            headers=headers,
            json={"vehicle_id": asset, "charge_grams": 1250, "ai_approved": True},
        ).status_code
        == 422
    )
    assert client.post("/api/v1/machines/execute", headers=headers, json={}).status_code == 404


def test_ingestion_idempotence_conflicts_units_and_audit(client):
    headers = register(client)
    capture = scan(client, headers, vehicle(client, headers))
    payload = VehicleSimulator().read_sample(1).model_dump(mode="json")
    endpoint = f"/api/v1/scans/{capture['id']}/telemetry"
    assert client.post(endpoint, headers=headers, json=payload).json()["status"] == "stored"
    assert client.post(endpoint, headers=headers, json=payload).json()["status"] == "duplicate"
    payload["readings"][0]["value"] = 2000
    assert client.post(endpoint, headers=headers, json=payload).status_code == 409
    payload["readings"][0]["unit"] = "V"
    assert client.post(endpoint, headers=headers, json=payload).status_code == 422
    actions = [entry["action"] for entry in client.get("/api/v1/audit", headers=headers).json()]
    assert "telemetry.ingested" in actions
    assert len(client.get(f"/api/v1/scans/{capture['id']}", headers=headers).json()["batches"]) == 2


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_scenarios_explicit_sample(client, scenario):
    headers = register(client)
    asset = vehicle(client, headers)
    result = client.post(
        "/api/v1/simulator/scans", headers=headers, json={"vehicle_id": asset, "scenario": scenario}
    ).json()
    assert result["origin"] == "SAMPLE"
    assert result["physical_connection"] is False
    assert result["batches"][0]["origin"] == "SAMPLE"
    if scenario == "sensor_fault":
        assert any(row["quality"] == "MISSING" for row in result["batches"][0]["readings"])
    if scenario == "disconnected":
        assert result["batches"][0]["readings"] == []


def test_invalid_credentials_duplicate_tenant_and_body_size(client):
    headers = register(client)
    duplicate = client.post(
        "/api/v1/auth/register",
        json={"organization": "test-workshop", "email": "other@example.test", "password": PASSWORD},
    )
    assert duplicate.status_code == 409
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"organization": "test-workshop", "email": "admin@example.test", "password": "incorrect-password"},
        ).status_code
        == 401
    )
    assert (
        client.post("/api/v1/vehicles", headers=headers, json={"name": "A", "organization_id": "spoofed"}).status_code
        == 422
    )
    assert client.post("/api/v1/vehicles", headers=headers, content=b"x" * 65537).status_code == 413


def test_rate_limit(tmp_path):
    with TestClient(create_app(f"sqlite:///{tmp_path / 'limit.db'}", "test", rate_limit=2)) as client:
        assert client.get("/api/v1/me").status_code == 401
        assert client.get("/api/v1/me").status_code == 401
        result = client.get("/api/v1/me")
        assert result.status_code == 429
        assert result.headers["Retry-After"] == "60"


def test_persistence_across_restart(tmp_path):
    url = f"sqlite:///{tmp_path / 'persistent.db'}"
    with TestClient(create_app(url, "test")) as client:
        headers = register(client)
        asset = vehicle(client, headers)
    with TestClient(create_app(url, "test")) as client:
        assert client.get("/api/v1/vehicles", headers=headers).json()[0]["id"] == asset


def test_production_rejects_sqlite():
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        create_app("sqlite:///unused.db", "production")
