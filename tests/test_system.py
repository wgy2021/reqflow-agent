from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_system_info() -> None:
    response = client.get("/system/info")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "reqflow-agent"
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"

    assert "llm_provider" in data
    assert "llm_model" in data

    assert data["database_type"] == "sqlite"
    assert data["tool_count"] == 3

    assert set(data["tools"]) == {
        "completeness_check",
        "ambiguity_check",
        "priority_suggestion",
    }

    assert data["cache_version"] == "v1"

    assert "api_key" not in data
    assert "llm_api_key" not in data