from fastapi.testclient import TestClient

from backend.services.api_gateway.main import app as api_gateway_app
from backend.services.auth_service.main import app as auth_app
from backend.services.scanner_service.main import app as scanner_app
from backend.services.ml_service.main import app as ml_app


def test_api_gateway_health():
    client = TestClient(api_gateway_app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'


def test_auth_service_health():
    client = TestClient(auth_app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['service'] == 'auth-service'


def test_scanner_service_health():
    client = TestClient(scanner_app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['service'] == 'scanner-service'


def test_ml_service_health():
    client = TestClient(ml_app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['service'] == 'ml-service'
