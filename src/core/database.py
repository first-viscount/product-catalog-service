"""Database configuration and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url
    or "postgresql+asyncpg://catalog_user:catalog_dev_password@localhost:5432/product_catalog_db",
    echo=settings.environment == "development",
    pool_size=getattr(settings, "db_pool_size", 10),
    max_overflow=getattr(settings, "db_pool_max_overflow", 20),
    pool_timeout=getattr(settings, "db_pool_timeout", 30),
    pool_pre_ping=True,
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for SQLAlchemy models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Dependency to get database session."""
    async with async_session() as session:
        try:
            # Update pool metrics if available
            _update_pool_metrics()
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def _update_pool_metrics() -> None:
    """Update database connection pool metrics."""
    try:
        # Import here to avoid circular imports
        from .metrics import get_metrics_collector

        metrics = get_metrics_collector()

        # Get pool statistics if available
        if hasattr(engine, "pool"):
            pool = engine.pool
            # Check if pool has the required metrics methods
            # QueuePool and AsyncAdaptedQueuePool have these, but NullPool and StaticPool don't
            if all(
                hasattr(pool, method) for method in ("size", "checkedout", "overflow")
            ):
                try:
                    # Call methods safely - they should not raise exceptions for valid pools
                    pool_size = pool.size()  # type: ignore[attr-defined]
                    checked_out = pool.checkedout()  # type: ignore[attr-defined]
                    overflow = pool.overflow()  # type: ignore[attr-defined]
                    metrics.update_db_pool_metrics(
                        pool_size=pool_size,
                        checked_out=checked_out,
                        overflow=overflow,
                    )
                except (AttributeError, TypeError):
                    # Handle case where methods exist but aren't callable or have wrong signature
                    logger.debug("Pool metrics methods are not callable", exc_info=True)
            else:
                # Pool doesn't support metrics (e.g., NullPool)
                logger.debug(
                    "Pool type %s does not support metrics collection",
                    type(pool).__name__,
                )
    except ImportError:
        # Metrics module not available
        logger.debug("Metrics collector not available")
    except Exception:  # pylint: disable=broad-exception-caught
        # Catch any other unexpected errors
        logger.debug("Could not update pool metrics", exc_info=True)


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession]:
    """Context manager to get database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database (create tables if needed)."""
    try:
        async with engine.begin() as conn:
            # In production, use Alembic migrations instead
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception:
        logger.exception("Failed to initialize database")
        raise


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
