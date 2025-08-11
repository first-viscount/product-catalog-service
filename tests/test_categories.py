"""Test category endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, sample_category_data):
    """Test creating a category."""
    response = await client.post("/api/v1/categories/", json=sample_category_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["name"] == sample_category_data["name"]
    assert data["description"] == sample_category_data["description"]
    assert data["path"] == sample_category_data["name"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_child_category(client: AsyncClient, sample_category_data):
    """Test creating a child category."""
    # First create a parent category
    parent_response = await client.post("/api/v1/categories/", json=sample_category_data)
    assert parent_response.status_code == 201
    parent_data = parent_response.json()
    
    # Create a child category
    child_data = {
        "name": "Smartphones",
        "description": "Mobile phones and smartphones",
        "parent_id": parent_data["id"]
    }
    
    response = await client.post("/api/v1/categories/", json=child_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["name"] == child_data["name"]
    assert data["parent_id"] == parent_data["id"]
    assert data["path"] == f"{parent_data['name']}/{child_data['name']}"


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, sample_category_data):
    """Test listing categories."""
    # Create a test category first
    await client.post("/api/v1/categories/", json=sample_category_data)
    
    response = await client.get("/api/v1/categories/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == sample_category_data["name"]


@pytest.mark.asyncio
async def test_get_category(client: AsyncClient, sample_category_data):
    """Test getting a specific category."""
    # Create a test category first
    create_response = await client.post("/api/v1/categories/", json=sample_category_data)
    created_data = create_response.json()
    category_id = created_data["id"]
    
    response = await client.get(f"/api/v1/categories/{category_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == category_id
    assert data["name"] == sample_category_data["name"]


@pytest.mark.asyncio
async def test_get_nonexistent_category(client: AsyncClient):
    """Test getting a non-existent category."""
    fake_id = "550e8400-e29b-41d4-a716-446655440000"
    response = await client.get(f"/api/v1/categories/{fake_id}")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient, sample_category_data):
    """Test updating a category."""
    # Create a test category first
    create_response = await client.post("/api/v1/categories/", json=sample_category_data)
    created_data = create_response.json()
    category_id = created_data["id"]
    
    # Update the category
    update_data = {"name": "Updated Electronics", "description": "Updated description"}
    response = await client.put(f"/api/v1/categories/{category_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["path"] == update_data["name"]  # Path should be updated too


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient, sample_category_data):
    """Test deleting a category."""
    # Create a test category first
    create_response = await client.post("/api/v1/categories/", json=sample_category_data)
    created_data = create_response.json()
    category_id = created_data["id"]
    
    # Delete the category
    response = await client.delete(f"/api/v1/categories/{category_id}")
    
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = await client.get(f"/api/v1/categories/{category_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_root_categories(client: AsyncClient, sample_category_data):
    """Test listing root categories."""
    # Create a root category
    await client.post("/api/v1/categories/", json=sample_category_data)
    
    response = await client.get("/api/v1/categories/root")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # All returned categories should have no parent_id
    for category in data:
        assert category["parent_id"] is None