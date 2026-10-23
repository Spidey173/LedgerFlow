import pytest
from fastapi.testclient import TestClient
import os

from scripts.api import app
import utils.config as config

client = TestClient(app)

def test_health_liveness():
    """Verify health endpoint returns 200 with service information."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "auth_enabled" in data

def test_health_readiness():
    """Verify readiness check reports connection and operational state."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "database_connected" in data
    assert "status" in data

def test_pagination_bounds(monkeypatch):
    """Verify API enforces safe bounds on limit parameter."""
    monkeypatch.setattr(config, "API_AUTH_ENABLED", False)
    # Test exceeding max limit (>200)
    response = client.get("/customers?limit=500")
    assert response.status_code == 422  # Pydantic validation error

    # Test negative limit
    response = client.get("/customers?limit=-5")
    assert response.status_code == 422

def test_database_failure_handling_without_demo_mode(monkeypatch):
    """Verify that when DEMO_MODE=False, database failure raises HTTP 503 instead of masking with demo data."""
    monkeypatch.setattr(config, "API_AUTH_ENABLED", False)
    monkeypatch.setattr(config, "DEMO_MODE", False)
    # Ensure get_db returns None
    monkeypatch.setattr("scripts.api.get_db", lambda: None)

    response = client.get("/customers")
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()

def test_database_failure_handling_with_explicit_demo_mode(monkeypatch):
    """Verify that when DEMO_MODE=True, fallback returns explicitly marked demo data."""
    monkeypatch.setattr(config, "API_AUTH_ENABLED", False)
    monkeypatch.setattr(config, "DEMO_MODE", True)
    monkeypatch.setattr("scripts.api.get_db", lambda: None)

    response = client.get("/customers?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "demo_mode_cache"
    assert len(data["data"]) <= 5

def test_api_authentication_enforcement(monkeypatch):
    """Verify endpoints enforce Bearer authentication when API_AUTH_ENABLED is True."""
    monkeypatch.setattr(config, "API_AUTH_ENABLED", True)
    monkeypatch.setattr(config, "API_KEYS", {
        "read-token-123": "read_only",
        "analyst-token-456": "analyst",
        "admin-token-789": "admin"
    })
    monkeypatch.setattr(config, "DEMO_MODE", True)
    monkeypatch.setattr("scripts.api.get_db", lambda: None)

    # 1. Unauthenticated request must receive 401
    resp_unauth = client.get("/customers")
    assert resp_unauth.status_code == 401

    # 2. Invalid token must receive 401
    resp_invalid = client.get("/customers", headers={"Authorization": "Bearer bad-token"})
    assert resp_invalid.status_code == 401

    # 3. Valid read_only token accesses /customers
    resp_auth = client.get("/customers", headers={"Authorization": "Bearer read-token-123"})
    assert resp_auth.status_code == 200

    # 4. Role authorization: read_only cannot access /dashboard (requires analyst)
    resp_forbidden = client.get("/dashboard", headers={"Authorization": "Bearer read-token-123"})
    assert resp_forbidden.status_code == 403

    # 5. Analyst token can access /dashboard
    resp_allowed = client.get("/dashboard", headers={"Authorization": "Bearer analyst-token-456"})
    assert resp_allowed.status_code == 200

def test_cors_restriction(monkeypatch):
    """Verify configured CORS allowed origins headers."""
    monkeypatch.setattr(config, "ALLOWED_ORIGINS", ["http://localhost:3000"])

    response = client.options("/customers", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code in (200, 204)
