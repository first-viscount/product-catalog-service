"""Test product endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, sample_category_data, sample_product_data):
    """Test creating a product."""
    # First create a category
    category_response = await client.post("/api/v1/categories/", json=sample_category_data)
    category_data = category_response.json()
    
    # Add category_id to product data
    product_data = sample_product_data.copy()
    product_data["category_id"] = category_data["id"]
    
    response = await client.post("/api/v1/products/", json=product_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["name"] == product_data["name"]
    assert data["description"] == product_data["description"]
    assert float(data["price"]) == product_data["price"]
    assert data["category_id"] == product_data["category_id"]
    assert data["attributes"] == product_data["attributes"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, sample_category_data, sample_product_data):
    """Test listing products."""
    # Create a category and product first
    category_response = await client.post("/api/v1/categories/", json=sample_category_data)
    category_data = category_response.json()
    
    product_data = sample_product_data.copy()
    product_data["category_id"] = category_data["id"]
    await client.post("/api/v1/products/", json=product_data)
    
    response = await client.get("/api/v1/products/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "products" in data
    assert "total" in data
    assert "offset" in data
    assert "limit" in data
    
    assert isinstance(data["products"], list)
    assert len(data["products"]) >= 1
    assert data["total"] >= 1
    
    # Check product has category information
    product = data["products"][0]
    assert "category" in product
    assert product["category"]["name"] == sample_category_data["name"]


@pytest.mark.asyncio
async def test_list_products_with_filters(client: AsyncClient, sample_category_data, sample_product_data):
    """Test listing products with filters."""
    # Create a category and product first
    category_response = await client.post("/api/v1/categories/", json=sample_category_data)
    category_data = category_response.json()
    
    product_data = sample_product_data.copy()
    product_data["category_id"] = category_data["id"]
    await client.post("/api/v1/products/", json=product_data)
    
    # Test filtering by category
    response = await client.get(f"/api/v1/products/?category_id={category_data['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["products"]) >= 1
    
    # Test filtering by price range
    response = await client.get(f"/api/v1/products/?min_price=20&max_price=50")
    assert response.status_code == 200
    data = response.json()
    assert len(data["products"]) >= 1
    
    # Test filtering by name
    response = await client.get(f"/api/v1/products/?name=Test")
    assert response.status_code == 200
    data = response.json()
    assert len(data["products"]) >= 1


@pytest.mark.asyncio
async def test_search_products(client: AsyncClient, sample_category_data, sample_product_data):
    """Test searching products."""
    # Create a category and product first
    category_response = await client.post("/api/v1/categories/", json=sample_category_data)
    category_data = category_response.json()
    
    product_data = sample_product_data.copy()
    product_data["category_id"] = category_data["id"]
    await client.post("/api/v1/products/", json=product_data)
    
    # Search for the product
    response = await client.get("/api/v1/products/search?q=Test")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "products" in data
    assert "total" in data
    assert "query" in data
    assert data["query"] == "Test"
    
    assert isinstance(data["products"], list)
    assert len(data["products"]) >= 1
    
    # Should find our test product
    found_product = data["products"][0]
    assert "Test" in found_product["name"]


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient, sample_category_data, sample_product_data):
    """Test getting a specific product."""
    # Create a category and product first
    category_response = await client.post("/api/v1/categories/", json=sample_category_data)
    category_data = category_response.json()
    
    product_data = sample_product_data.copy()
    product_data["category_id"] = category_data["id"]
    create_response = await client.post("/api/v1/products/", json=product_data)
    created_data = create_response.json()
    product_id = created_data["id"]
    
    response = await client.get(f"/api/v1/products/{product_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == product_id
    assert data["name"] == product_data["name"]
    assert "category" in data
    assert data["category"]["name"] == sample_category_data["name"]


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, sample_category_data, sample_product_data):
    """Test updating a product."""
    # Create a category and product first
    category_response = await client.post("/api/v1/categories/", json=sample_category_data)
    category_data = category_response.json()
    
    product_data = sample_product_data.copy()
    product_data["category_id"] = category_data["id"]
    create_response = await client.post("/api/v1/products/", json=product_data)
    created_data = create_response.json()
    product_id = created_data["id"]
    
    # Update the product
    update_data = {
        "name": "Updated Product",
        "price": 39.99,
        "attributes": {"color": "red", "size": "large"}
    }
    response = await client.put(f"/api/v1/products/{product_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == update_data["name"]
    assert float(data["price"]) == update_data["price"]
    assert data["attributes"] == update_data["attributes"]


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient, sample_category_data, sample_product_data):
    """Test deleting a product."""
    # Create a category and product first
    category_response = await client.post("/api/v1/categories/", json=sample_category_data)
    category_data = category_response.json()
    
    product_data = sample_product_data.copy()
    product_data["category_id"] = category_data["id"]
    create_response = await client.post("/api/v1/products/", json=product_data)
    created_data = create_response.json()
    product_id = created_data["id"]
    
    # Delete the product
    response = await client.delete(f"/api/v1/products/{product_id}")
    
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = await client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_product(client: AsyncClient):
    """Test getting a non-existent product."""
    fake_id = "550e8400-e29b-41d4-a716-446655440000"
    response = await client.get(f"/api/v1/products/{fake_id}")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_price_range(client: AsyncClient):
    """Test invalid price range filter."""
    response = await client.get("/api/v1/products/?min_price=50&max_price=20")
    
    assert response.status_code == 400
    assert "min_price cannot be greater than max_price" in response.json()["message"]