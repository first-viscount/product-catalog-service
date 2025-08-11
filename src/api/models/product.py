"""Pydantic models for product API."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """Base category schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Category name")
    parent_id: UUID | None = Field(None, description="Parent category ID")
    description: str | None = Field(None, description="Category description")


class CategoryCreate(CategoryBase):
    """Category creation schema."""
    pass


class CategoryUpdate(BaseModel):
    """Category update schema."""
    name: str | None = Field(None, min_length=1, max_length=255, description="Category name")
    parent_id: UUID | None = Field(None, description="Parent category ID")
    description: str | None = Field(None, description="Category description")


class Category(CategoryBase):
    """Category response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    path: str = Field(..., description="Category path (e.g., 'Electronics/Computers')")
    created_at: datetime
    updated_at: datetime


class CategoryWithChildren(Category):
    """Category with children schema."""
    children: list["CategoryWithChildren"] = Field(default_factory=list)


class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: str | None = Field(None, description="Product description")
    category_id: UUID = Field(..., description="Category ID")
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Product price")
    stock_quantity: int = Field(0, ge=0, description="Stock quantity")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Product attributes")


class ProductCreate(ProductBase):
    """Product creation schema."""
    pass


class ProductUpdate(BaseModel):
    """Product update schema."""
    name: str | None = Field(None, min_length=1, max_length=255, description="Product name")
    description: str | None = Field(None, description="Product description")
    category_id: UUID | None = Field(None, description="Category ID")
    price: Decimal | None = Field(None, ge=0, decimal_places=2, description="Product price")
    stock_quantity: int | None = Field(None, ge=0, description="Stock quantity")
    attributes: dict[str, Any] | None = Field(None, description="Product attributes")


class Product(ProductBase):
    """Product response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class ProductWithCategory(Product):
    """Product with category schema."""
    category: Category


class ProductSearchParams(BaseModel):
    """Product search parameters."""
    q: str = Field(..., min_length=1, description="Search query")
    category_id: UUID | None = Field(None, description="Filter by category")
    offset: int = Field(0, ge=0, description="Pagination offset")
    limit: int = Field(50, ge=1, le=100, description="Pagination limit")


class ProductListParams(BaseModel):
    """Product list parameters."""
    category_id: UUID | None = Field(None, description="Filter by category")
    min_price: Decimal | None = Field(None, ge=0, description="Minimum price filter")
    max_price: Decimal | None = Field(None, ge=0, description="Maximum price filter")
    name: str | None = Field(None, description="Filter by name (partial match)")
    offset: int = Field(0, ge=0, description="Pagination offset")
    limit: int = Field(50, ge=1, le=100, description="Pagination limit")


class ProductListResponse(BaseModel):
    """Product list response with pagination."""
    products: list[ProductWithCategory]
    total: int = Field(..., description="Total number of products")
    offset: int = Field(..., description="Current offset")
    limit: int = Field(..., description="Current limit")


class ProductSearchResponse(BaseModel):
    """Product search response with pagination."""
    products: list[ProductWithCategory]
    total: int = Field(..., description="Total number of matching products")
    offset: int = Field(..., description="Current offset")
    limit: int = Field(..., description="Current limit")
    query: str = Field(..., description="Search query used")