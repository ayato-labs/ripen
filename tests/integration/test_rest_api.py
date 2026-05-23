import pytest
from starlette.testclient import TestClient

from ripen.api.server import mcp


@pytest.fixture
def client():
    # Retrieve the Starlette app from FastMCP
    app = mcp.http_app()
    return TestClient(app)


@pytest.mark.asyncio
async def test_rest_api_save_and_read_flow(client, monkeypatch):
    """
    Test saving and reading memories via REST API endpoints.
    """
    # 1. Setup environment variables for AuthMiddleware (EnvAuthProvider)
    monkeypatch.setenv("RIPEN_API_KEY", "test-rest-key")
    monkeypatch.setenv("RIPEN_ACCOUNT", "rest_test_user")

    headers = {
        "x-api-key": "test-rest-key",
        "x-ripen-agent-id": "rest-agent-id"
    }

    # 2. Save memory via POST /api/v1alpha2/memories
    payload = {
        "entities": [
            {"name": "RestNode", "entity_type": "Node", "description": "Created via REST API"}
        ],
        "relations": [],
        "observations": [
            {"entity_name": "RestNode", "content": "REST API is functional"}
        ],
        "bank_files": []
    }

    response = client.post("/api/v1alpha2/memories", json=payload, headers=headers)
    assert response.status_code == 200, f"Response: {response.text}"
    assert response.json()["status"] == "success"

    # 3. Read memory via GET /api/v1alpha2/memories
    response = client.get("/api/v1alpha2/memories?query=RestNode", headers=headers)
    assert response.status_code == 200, f"Response: {response.text}"
    
    data = response.json()
    assert data["status"] == "success"
    assert "results" in data
    
    # Verify entity was saved and retrieved
    results = data["results"]
    assert "graph" in results
    graph_data = results["graph"]
    assert "entities" in graph_data
    entity_names = [e["name"] for e in graph_data["entities"]]
    assert "RestNode" in entity_names

    # 4. Verification of Authentication Failures
    bad_headers = {
        "x-api-key": "invalid-key"
    }
    response = client.post("/api/v1alpha2/memories", json=payload, headers=bad_headers)
    assert response.status_code == 401
    assert "Authentication required" in response.json()["message"]
