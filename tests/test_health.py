"""Test health endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test the health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["service"] == "product-catalog-service"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test the readiness check endpoint."""
    response = await client.get("/health/ready")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ready"] is True
    assert data["service"] == "product-catalog-service"
    assert data["version"] == "0.1.0"
    assert "checks" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test the root endpoint."""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["service"] == "product-catalog-service"
    assert data["version"] == "0.1.0"
    assert "database" in data


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    """Test the metrics endpoint."""
    response = await client.get("/metrics")
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    
    # Check that prometheus metrics format is returned
    content = response.text
    assert "# HELP" in content or "# TYPE" in content