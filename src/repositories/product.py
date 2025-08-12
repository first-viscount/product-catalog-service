"""Repository for product operations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.product import Product
from .base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository for product operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository."""
        super().__init__(session)

    async def create(self, **kwargs: Any) -> Product:
        """Create a new product."""
        product = Product(**kwargs)

        # Create search vector for basic text search
        search_text = f"{product.name} {product.description or ''}"
        product.search_vector = search_text.lower()

        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get(self, id: UUID) -> Product | None:
        """Get product by ID."""
        stmt = select(Product).where(Product.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_category(self, id: UUID) -> Product | None:
        """Get product with category loaded."""
        stmt = (
            select(Product)
            .where(Product.id == id)
            .options(selectinload(Product.category))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, id: UUID, **kwargs: Any) -> Product | None:
        """Update product."""
        product = await self.get(id)
        if not product:
            return None

        # Update fields
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)

        # Update search vector if name or description changed
        if "name" in kwargs or "description" in kwargs:
            search_text = f"{product.name} {product.description or ''}"
            product.search_vector = search_text.lower()

        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def delete(self, id: UUID) -> bool:
        """Delete product."""
        product = await self.get(id)
        if not product:
            return False

        await self.session.delete(product)
        return True

    async def list(
        self,
        offset: int = 0,
        limit: int = 50,
        category_id: UUID | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        **filters: Any,
    ) -> list[Product]:
        """List products with pagination and filters."""
        stmt = select(Product).options(selectinload(Product.category))

        # Apply filters
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)

        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)

        if name := filters.get("name"):
            stmt = stmt.where(Product.name.ilike(f"%{name}%"))

        # Default ordering by created_at desc (newest first)
        stmt = stmt.order_by(Product.created_at.desc())

        # Apply pagination
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        category_id: UUID | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        **filters: Any,
    ) -> int:
        """Count products with filters."""
        stmt = select(func.count(Product.id))

        # Apply same filters as list method
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)

        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)

        if name := filters.get("name"):
            stmt = stmt.where(Product.name.ilike(f"%{name}%"))

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def search(
        self,
        query: str,
        offset: int = 0,
        limit: int = 50,
        category_id: UUID | None = None,
    ) -> list[Product]:
        """Search products by text query."""
        search_term = query.lower().strip()

        stmt = (
            select(Product)
            .options(selectinload(Product.category))
            .where(
                or_(
                    Product.name.ilike(f"%{search_term}%"),
                    Product.description.ilike(f"%{search_term}%"),
                    Product.search_vector.ilike(f"%{search_term}%"),
                ),
            )
        )

        # Apply category filter if specified
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)

        # Order by relevance - simple approach compatible with all databases
        # Exact matches first, then name starting with term, then containing term, then rest
        stmt = stmt.order_by(
            Product.name.ilike(search_term).desc(),  # Exact matches first
            Product.name.ilike(f"{search_term}%").desc(),  # Starts with term
            Product.name.ilike(f"%{search_term}%").desc(),  # Contains term
            Product.created_at.desc(),  # Most recent first
        )

        # Apply pagination
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_count(
        self,
        query: str,
        category_id: UUID | None = None,
    ) -> int:
        """Count search results."""
        search_term = query.lower().strip()

        stmt = select(func.count(Product.id)).where(
            or_(
                Product.name.ilike(f"%{search_term}%"),
                Product.description.ilike(f"%{search_term}%"),
                Product.search_vector.ilike(f"%{search_term}%"),
            ),
        )

        if category_id:
            stmt = stmt.where(Product.category_id == category_id)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def list_by_category(
        self,
        category_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Product]:
        """List products in a specific category."""
        return await self.list(
            offset=offset,
            limit=limit,
            category_id=category_id,
        )
