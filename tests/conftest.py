"""Test configuration and fixtures."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.database import Base, get_db
from src.main import app

# Import models to register them with Base - must be imported after Base is created

# Test database URL - use temporary file SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_product_catalog.db"


@pytest_asyncio.fixture(scope="function")
async def test_db_engine() -> AsyncGenerator[None]:
    """Create a test database engine."""
    import os

    # Remove test database file if it exists
    test_db_file = "./test_product_catalog.db"
    if os.path.exists(test_db_file):
        os.remove(test_db_file)

    # Ensure models are imported before creating tables

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()

    # Remove test database file after test
    if os.path.exists(test_db_file):
        os.remove(test_db_file)


@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_db_engine) -> AsyncGenerator[AsyncClient]:
    """Create a test client with test database."""

    # Create session maker with the test engine
    TestSessionLocal = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def get_test_db() -> AsyncGenerator[AsyncSession]:
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test",
    ) as client:
        yield client

    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def sample_category_data() -> dict[str, str]:
    """Sample category data for testing."""
    return {
        "name": "Electronics",
        "description": "Electronic devices and accessories",
    }


@pytest.fixture
def sample_product_data() -> dict[str, str | float | int | dict[str, str]]:
    """Sample product data for testing."""
    return {
        "name": "Test Product",
        "description": "A test product for testing purposes",
        "price": 29.99,
        "stock_quantity": 100,
        "attributes": {
            "color": "blue",
            "size": "medium",
        },
    }
