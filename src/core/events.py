"""Event logging service for Product Catalog Service.

For Phase 1 MVP, events are logged rather than published to external systems.
This makes the service self-contained without external dependencies.
"""

import uuid
from decimal import Decimal
from typing import Any

import structlog

# from ..models.events import (
from ..models.events import (
    PriceChangeData,
    PriceChangedEvent,
    ProductCreatedEvent,
    ProductData,
    ProductDeletedData,
    ProductDeletedEvent,
    ProductOutOfStockData,
    ProductOutOfStockEvent,
    ProductUpdatedEvent,
)

logger = structlog.get_logger(__name__)


class ProductCatalogEventService:
    """
    Event logging service for Product Catalog Service.

    For Phase 1 MVP, logs events for product lifecycle changes including:
    - Product creation, updates, and deletion
    - Price changes
    - Stock status changes

    In future phases, this can be extended to publish to external systems.
    """

    def __init__(self) -> None:
        """Initialize the event service."""
        self.logger = logger.bind(component="event_service")

    async def start(self) -> None:
        """Start the event service (no-op for logging implementation)."""
        self.logger.info("Event service started (logging mode)")

    async def stop(self) -> None:
        """Stop the event service (no-op for logging implementation)."""
        self.logger.info("Event service stopped")

    async def publish_product_created(
        self,
        product_id: str,
        name: str,
        description: str | None,
        category_id: str,
        price: Decimal,
        sku: str | None = None,
        is_active: bool = True,
        attributes: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Log ProductCreated event."""
        try:
            # Create event data
            product_data = ProductData(
                product_id=product_id,
                name=name,
                description=description,
                category_id=category_id,
                price=price,
                sku=sku,
                is_active=is_active,
                attributes=attributes or {},
            )

            # Create event
            event = ProductCreatedEvent(
                correlation_id=correlation_id or str(uuid.uuid4()),
                data=product_data.model_dump(),
            )

            # Log event instead of publishing
            self.logger.info(
                "ProductCreated event logged",
                event_type=event.event_type,
                event_id=event.event_id,
                correlation_id=event.correlation_id,
                product_id=product_id,
                product_name=name,
                price=str(price),
                category_id=category_id,
            )

        except Exception:
            self.logger.exception(
                "Failed to log ProductCreated event",
                product_id=product_id,
            )

    async def publish_product_updated(
        self,
        product_id: str,
        name: str,
        description: str | None,
        category_id: str,
        price: Decimal,
        sku: str | None = None,
        is_active: bool = True,
        attributes: dict[str, Any] | None = None,
        changes: list[dict[str, Any]] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Log ProductUpdated event."""
        try:
            # Create event data
            product_data = ProductData(
                product_id=product_id,
                name=name,
                description=description,
                category_id=category_id,
                price=price,
                sku=sku,
                is_active=is_active,
                attributes=attributes or {},
            )

            # Create event
            event_data = product_data.model_dump()
            if changes:
                event_data["changes"] = changes

            event = ProductUpdatedEvent(
                correlation_id=correlation_id or str(uuid.uuid4()),
                data=event_data,
            )

            # Log event instead of publishing
            self.logger.info(
                "ProductUpdated event logged",
                event_type=event.event_type,
                event_id=event.event_id,
                correlation_id=event.correlation_id,
                product_id=product_id,
                product_name=name,
                changes_count=len(changes) if changes else 0,
                changes=changes if changes else [],
            )

        except Exception:
            self.logger.exception(
                "Failed to log ProductUpdated event",
                product_id=product_id,
            )

    async def publish_product_deleted(
        self,
        product_id: str,
        name: str | None = None,
        reason: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Log ProductDeleted event."""
        try:
            # Create event data
            event_data = ProductDeletedData(
                product_id=product_id,
                name=name,
                reason=reason,
            )

            # Create event
            event = ProductDeletedEvent(
                correlation_id=correlation_id or str(uuid.uuid4()),
                data=event_data.model_dump(),
            )

            # Log event instead of publishing
            self.logger.info(
                "ProductDeleted event logged",
                event_type=event.event_type,
                event_id=event.event_id,
                correlation_id=event.correlation_id,
                product_id=product_id,
                product_name=name,
                reason=reason,
            )

        except Exception:
            self.logger.exception(
                "Failed to log ProductDeleted event",
                product_id=product_id,
            )

    async def publish_price_changed(
        self,
        product_id: str,
        old_price: Decimal,
        new_price: Decimal,
        effective_date: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Log PriceChanged event."""
        try:
            # Create event data
            price_data = PriceChangeData(
                product_id=product_id,
                old_price=old_price,
                new_price=new_price,
                effective_date=effective_date,
            )

            # Create event
            event = PriceChangedEvent(
                correlation_id=correlation_id or str(uuid.uuid4()),
                data=price_data.model_dump(),
            )

            # Log event instead of publishing
            self.logger.info(
                "PriceChanged event logged",
                event_type=event.event_type,
                event_id=event.event_id,
                correlation_id=event.correlation_id,
                product_id=product_id,
                old_price=str(old_price),
                new_price=str(new_price),
                effective_date=effective_date,
            )

        except Exception:
            self.logger.exception(
                "Failed to log PriceChanged event",
                product_id=product_id,
            )

    async def publish_product_out_of_stock(
        self,
        product_id: str,
        last_stock_level: int,
        location_id: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Log ProductOutOfStock event."""
        try:
            # Create event data
            stock_data = ProductOutOfStockData(
                product_id=product_id,
                last_stock_level=last_stock_level,
                location_id=location_id,
            )

            # Create event
            event = ProductOutOfStockEvent(
                correlation_id=correlation_id or str(uuid.uuid4()),
                data=stock_data.model_dump(),
            )

            # Log event instead of publishing
            self.logger.info(
                "ProductOutOfStock event logged",
                event_type=event.event_type,
                event_id=event.event_id,
                correlation_id=event.correlation_id,
                product_id=product_id,
                last_stock_level=last_stock_level,
                location_id=location_id,
            )

        except Exception:
            self.logger.exception(
                "Failed to log ProductOutOfStock event",
                product_id=product_id,
            )


# Global instance
_event_service: ProductCatalogEventService | None = None


async def get_event_service() -> ProductCatalogEventService:
    """Get or create the global event service instance."""
    global _event_service
    if _event_service is None:
        _event_service = ProductCatalogEventService()
        await _event_service.start()
    return _event_service


async def close_event_service() -> None:
    """Close the global event service instance."""
    global _event_service
    if _event_service is not None:
        await _event_service.stop()
        _event_service = None
