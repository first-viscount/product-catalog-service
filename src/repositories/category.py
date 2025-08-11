"""Repository for category operations."""

from __future__ import annotations

from uuid import UUID
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.product import Category
from src.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository for category operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository."""
        super().__init__(session)

    async def create(self, **kwargs: Any) -> Category:
        """Create a new category."""
        category = Category(**kwargs)
        
        # Generate path based on parent
        if category.parent_id:
            parent = await self.get(category.parent_id)
            if parent:
                category.path = f"{parent.path}/{category.name}"
            else:
                raise ValueError("Parent category not found")
        else:
            category.path = category.name
        
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def get(self, id: UUID) -> Category | None:
        """Get category by ID."""
        stmt = select(Category).where(Category.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_children(self, id: UUID) -> Category | None:
        """Get category with children loaded."""
        stmt = (
            select(Category)
            .where(Category.id == id)
            .options(selectinload(Category.children))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, id: UUID, **kwargs: Any) -> Category | None:
        """Update category."""
        category = await self.get(id)
        if not category:
            return None

        # Update fields
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)

        # Regenerate path if name or parent changed
        if "name" in kwargs or "parent_id" in kwargs:
            if category.parent_id:
                parent = await self.get(category.parent_id)
                if parent:
                    category.path = f"{parent.path}/{category.name}"
                else:
                    raise ValueError("Parent category not found")
            else:
                category.path = category.name

        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def delete(self, id: UUID) -> bool:
        """Delete category."""
        category = await self.get(id)
        if not category:
            return False

        await self.session.delete(category)
        return True

    async def list(self, **filters: Any) -> list[Category]:
        """List categories with optional filters."""
        stmt = select(Category)

        if parent_id := filters.get("parent_id"):
            stmt = stmt.where(Category.parent_id == parent_id)

        if name := filters.get("name"):
            stmt = stmt.where(Category.name.ilike(f"%{name}%"))

        # Default ordering by name
        stmt = stmt.order_by(Category.name)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_root_categories(self) -> list[Category]:
        """List root categories (no parent)."""
        stmt = (
            select(Category)
            .where(Category.parent_id.is_(None))
            .order_by(Category.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_path(self, path: str) -> Category | None:
        """Get category by path."""
        stmt = select(Category).where(Category.path == path)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()