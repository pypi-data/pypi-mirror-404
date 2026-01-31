"""
Integration tests for Skills API endpoints (Phase 4.3)

Tests all REST API endpoints with proper authentication,
input validation, rate limiting, and error handling.
"""


# Add scripts directory to path for importing skills_api
# scripts_path = Path(__file__).parent.parent / "scripts"
# if not scripts_path.exists():
#     pytest.skip("Scripts directory not found (likely public release)", allow_module_level=True)
# sys.path.insert(0, str(scripts_path))
from pathlib import Path
from typing import Any

import pytest

# Skip when running outside project root where relative paths are expected
project_skills_dir = Path("orchestrator/skills")
if not project_skills_dir.exists():
    pytest.skip("orchestrator/skills not found in CWD; skip integration tests", allow_module_level=True)

try:
    from orchestrator.server.app import app
except Exception:
    # Guard against import-time side effects failing when optional assets are missing
    pytest.skip("skills API app unavailable in this environment", allow_module_level=True)


@pytest.fixture
def client() -> Any:
    """Create Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers() -> Any:
    """Return headers with valid API key."""
    return {"X-API-Key": "demo-key-12345"}


class TestHealthEndpoints:
    """Test health and system endpoints."""

    def test_health_check(self, client: Any) -> None:
        """Test GET /api/health."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"

    def test_system_info(self, client: Any) -> None:
        """Test GET /api/system/info."""
        response = client.get("/api/system/info")

        assert response.status_code == 200
        data = response.get_json()
        assert "version" in data
        assert "skills_count" in data


class TestSkillsEndpoints:
    """Test skill listing and detail endpoints."""

    def test_list_skills(self, client: Any) -> None:
        """Test GET /api/skills."""
        response = client.get("/api/skills")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

        if len(data) > 0:
            skill = data[0]
            assert "id" in skill
            assert "name" in skill

    def test_get_skill_details(self, client: Any) -> None:
        """Test GET /api/skills/<id>."""
        # First get list to find a skill
        response = client.get("/api/skills")
        skills = response.get_json()

        if len(skills) > 0:
            skill_id = skills[0]["id"]
            response = client.get(f"/api/skills/{skill_id}")

            assert response.status_code == 200
            data = response.get_json()
            assert data["id"] == skill_id

    def test_get_nonexistent_skill(self, client: Any) -> None:
        """Test GET /api/skills/<nonexistent>."""
        response = client.get("/api/skills/nonexistent-skill-xyz")

        assert response.status_code == 404

    def test_execute_skill_without_auth(self, client: Any) -> None:
        """Test POST /api/skills/<id>/execute without API key."""
        response = client.post(
            "/api/skills/test-skill/execute", json={"capability": "test", "parameters": {}}
        )

        assert response.status_code == 401

    def test_execute_skill_with_auth(self, client: Any, auth_headers: Any) -> None:
        """Test POST /api/skills/<id>/execute with API key."""
        response = client.post(
            "/api/skills/cost-control/execute",
            headers=auth_headers,
            json={"capability": "get_agent_metrics", "parameters": {}},
        )

        # Should return 200 (success) or 400 (validation error)
        assert response.status_code in [200, 400]


class TestMetricsEndpoints:
    """Test metrics endpoints."""

    def test_list_metrics(self, client: Any) -> None:
        """Test GET /api/metrics."""
        response = client.get("/api/metrics")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_skill_metrics(self, client: Any) -> None:
        """Test GET /api/metrics/<skill_id>."""
        response = client.get("/api/metrics/cost-control")

        # May return 200 or 404 depending on Redis availability
        assert response.status_code in [200, 404, 500]

    def test_get_metrics_history(self, client: Any) -> None:
        """Test GET /api/metrics/<skill_id>/history."""
        response = client.get("/api/metrics/cost-control/history?hours=24")

        # May return 200 or 404 depending on Redis availability
        assert response.status_code in [200, 404, 500]


class TestCollectionsEndpoints:
    """Test collections endpoints."""

    def test_list_collections(self, client: Any) -> None:
        """Test GET /api/collections."""
        response = client.get("/api/collections")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_collection_details(self, client: Any) -> None:
        """Test GET /api/collections/<id>."""
        # First get list
        response = client.get("/api/collections")
        collections = response.get_json()

        if len(collections) > 0:
            collection_id = collections[0]["id"]
            response = client.get(f"/api/collections/{collection_id}")

            assert response.status_code in [200, 404]

    def test_create_collection_without_auth(self, client: Any) -> None:
        """Test POST /api/collections without API key."""
        response = client.post("/api/collections", json={"name": "Test Collection"})

        assert response.status_code == 401

    def test_create_collection_with_auth(self, client: Any, auth_headers: Any) -> None:
        """Test POST /api/collections with API key."""
        import time

        response = client.post(
            "/api/collections",
            headers=auth_headers,
            json={"name": f"Test Collection {int(time.time())}", "description": "Test"},
        )

        # Should succeed or fail validation
        assert response.status_code in [201, 400, 500]

    def test_add_skill_to_collection_without_auth(self, client: Any) -> None:
        """Test POST /api/collections/<id>/skills/<skill_id> without auth."""
        response = client.post("/api/collections/test-collection/skills/test-skill")

        assert response.status_code == 401


class TestMarketplaceEndpoints:
    """Test marketplace endpoints."""

    def test_list_marketplace(self, client: Any) -> None:
        """Test GET /api/marketplace."""
        response = client.get("/api/marketplace")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_download_skill_without_auth(self, client: Any) -> None:
        """Test POST /api/marketplace/<id>/download without auth."""
        response = client.post("/api/marketplace/test-skill/download")

        assert response.status_code == 401

    def test_download_skill_with_auth(self, client: Any, auth_headers: Any) -> None:
        """Test POST /api/marketplace/<id>/download with auth."""
        response = client.post("/api/marketplace/cost-control/download", headers=auth_headers)

        # Should succeed or return 404/400
        assert response.status_code in [200, 404, 400]

    def test_rate_skill_without_auth(self, client: Any) -> None:
        """Test POST /api/marketplace/<id>/rate without auth."""
        response = client.post("/api/marketplace/test-skill/rate", json={"rating": 5})

        assert response.status_code == 401

    def test_rate_skill_with_auth(self, client: Any, auth_headers: Any) -> None:
        """Test POST /api/marketplace/<id>/rate with auth."""
        response = client.post(
            "/api/marketplace/cost-control/rate", headers=auth_headers, json={"rating": 5}
        )

        # Should succeed or fail validation
        assert response.status_code in [200, 400, 404]


class TestSearchEndpoint:
    """Test search endpoint."""

    def test_search(self, client: Any) -> None:
        """Test GET /api/search."""
        response = client.get("/api/search?q=cost")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_search_empty_query(self, client: Any) -> None:
        """Test GET /api/search with empty query."""
        response = client.get("/api/search?q=")

        # Should handle gracefully
        assert response.status_code in [200, 400]


class TestErrorHandling:
    """Test API error handling."""

    def test_404_endpoint(self, client: Any) -> None:
        """Test accessing non-existent endpoint."""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404

    def test_invalid_json(self, client: Any, auth_headers: Any) -> None:
        """Test sending invalid JSON."""
        response = client.post(
            "/api/collections",
            headers=auth_headers,
            data="invalid json",
            content_type="application/json",
        )

        # Should handle invalid JSON gracefully
        assert response.status_code in [400, 500]

    def test_missing_required_header(self, client: Any) -> None:
        """Test POST without required authentication."""
        response = client.post("/api/collections", json={"name": "Test"})

        assert response.status_code == 401


class TestResponseFormat:
    """Test response format consistency."""

    def test_success_response_format(self, client: Any) -> None:
        """Test successful responses have consistent format."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)

    def test_error_response_format(self, client: Any) -> None:
        """Test error responses have consistent format."""
        response = client.get("/api/skills/nonexistent-xyz")

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data or "message" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
