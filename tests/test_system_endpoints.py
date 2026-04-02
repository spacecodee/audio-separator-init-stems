from fastapi.testclient import TestClient

from main import app  # noqa: E402

client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_models_endpoint_exposes_defaults() -> None:
    response = client.get("/models")
    assert response.status_code == 200
    payload = response.json()
    assert "models" in payload
    assert "effects_default" in payload
    assert payload["effects_default"]["dereverb"] == "dereverb_mel"
