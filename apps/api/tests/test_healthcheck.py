from bodyos_api.app import create_app
from fastapi.testclient import TestClient


def test_healthcheck_reports_owner_alpha_version() -> None:
    client = TestClient(create_app())

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "v2.0.0-alpha.1"}
