"""SQLAlchemy models for product catalog."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID as UUID_TYPE
from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import CHAR, TypeDecorator

from ..core.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(32).
    Stores as string for SQLite compatibility in tests.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeDecorator:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))  # String format for SQLite

    def process_bind_param(self, value, dialect) -> str | UUID_TYPE | None:
        if value is None or dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value, dialect) -> UUID_TYPE | None:
        if value is None or dialect.name == "postgresql":
            return value
        return UUID_TYPE(value) if isinstance(value, str) else value


class Category(Base):
    """Category model for product organization."""

    __tablename__ = "categories"

    # Primary identification
    id: Mapped[UUID_TYPE] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Hierarchical structure
    parent_id: Mapped[UUID_TYPE | None] = mapped_column(
        GUID(),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
    )
    path: Mapped[str] = mapped_column(
        String(1000), nullable=False,
    )  # For efficient querying

    # Metadata
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    parent: Mapped["Category | None"] = relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category",
    )

    # Indexes for efficient queries
    __table_args__ = (
        Index("ix_categories_name", "name"),
        Index("ix_categories_parent_id", "parent_id"),
        Index("ix_categories_path", "path"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Category {self.name} [{self.path}]>"


class Product(Base):
    """Product model for the catalog."""

    __tablename__ = "products"

    # Primary identification
    id: Mapped[UUID_TYPE] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Categorization
    category_id: Mapped[UUID_TYPE] = mapped_column(
        GUID(),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Pricing
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        info={
            "check_constraints": [CheckConstraint("price >= 0", name="positive_price")],
        },
    )

    # Inventory
    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        info={
            "check_constraints": [
                CheckConstraint("stock_quantity >= 0", name="non_negative_stock"),
            ],
        },
    )

    # Product attributes stored as JSON
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)

    # Search optimization
    search_vector: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )  # For full-text search

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")

    # Indexes for efficient queries
    __table_args__ = (
        Index("ix_products_name", "name"),
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_price", "price"),
        Index("ix_products_created_at", "created_at"),
        Index("ix_products_stock_quantity", "stock_quantity"),
        # Full-text search index would be added via migration
        CheckConstraint("price >= 0", name="positive_price"),
        CheckConstraint("stock_quantity >= 0", name="non_negative_stock"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Product {self.name} [${self.price}]>"
