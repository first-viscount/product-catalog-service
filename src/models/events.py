"""Internal event models for Product Catalog Service.

These models replace the external first_viscount_events dependency to make
the service self-contained for Phase 1 MVP. Events are logged rather than
published to external systems.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base event model with common fields."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_service: str = "product-catalog-service"
    event_version: str = "1.0"


class ProductData(BaseModel):
    """Product data payload for events."""

    product_id: str
    name: str
    description: str | None = None
    category_id: str
    price: Decimal
    sku: str | None = None
    is_active: bool = True
    attributes: dict[str, Any] = Field(default_factory=dict)


class ProductCreatedEvent(BaseEvent):
    """Event published when a product is created."""

    event_type: str = "product.created"
    data: dict[str, Any]


class ProductUpdatedEvent(BaseEvent):
    """Event published when a product is updated."""

    event_type: str = "product.updated"
    data: dict[str, Any]


class ProductDeletedEvent(BaseEvent):
    """Event published when a product is deleted."""

    event_type: str = "product.deleted"
    data: dict[str, Any]


class PriceChangedEvent(BaseEvent):
    """Event published when a product's price changes."""

    event_type: str = "product.price_changed"
    data: dict[str, Any]


class ProductOutOfStockEvent(BaseEvent):
    """Event published when a product goes out of stock."""

    event_type: str = "product.out_of_stock"
    data: dict[str, Any]


# Data models for specific event payloads


class ProductDeletedData(BaseModel):
    """Data payload for ProductDeleted events."""

    product_id: str
    name: str | None = None
    reason: str | None = None


class PriceChangeData(BaseModel):
    """Data payload for PriceChanged events."""

    product_id: str
    old_price: Decimal
    new_price: Decimal
    effective_date: str | None = None


class ProductOutOfStockData(BaseModel):
    """Data payload for ProductOutOfStock events."""

    product_id: str
    last_stock_level: int
    location_id: str | None = None


class ProductChangeData(BaseModel):
    """Data for tracking field changes in product updates."""

    field: str
    old_value: Any
    new_value: Any
