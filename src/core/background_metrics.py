"""Background tasks for updating metrics."""

import asyncio

from sqlalchemy import func, select

from ..models.product import Category, Product
from .database import get_db_context
from .logging import get_logger
from .metrics import get_metrics_collector

logger = get_logger(__name__)


class BackgroundMetricsUpdater:
    """Background service to update metrics that require database queries."""

    def __init__(self, update_interval: int = 30) -> None:
        """Initialize the background metrics updater.

        Args:
            update_interval: Interval in seconds between metric updates
        """
        self.update_interval = update_interval
        self.metrics = get_metrics_collector()
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the background metrics update task."""
        if self._running:
            logger.warning("Background metrics updater is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._update_loop())
        logger.info("Background metrics updater started", interval=self.update_interval)

    async def stop(self) -> None:
        """Stop the background metrics update task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Background metrics updater stopped")

    async def _update_loop(self) -> None:
        """Main update loop for background metrics."""
        while self._running:
            try:
                await self._update_catalog_metrics()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error updating background metrics")
                await asyncio.sleep(self.update_interval)

    async def _update_catalog_metrics(self) -> None:
        """Update product catalog metrics."""
        try:
            async with get_db_context() as session:
                # Count total products
                product_count_stmt = select(func.count(Product.id))
                product_result = await session.execute(product_count_stmt)
                total_products = product_result.scalar_one()

                # Count total categories
                category_count_stmt = select(func.count(Category.id))
                category_result = await session.execute(category_count_stmt)
                total_categories = category_result.scalar_one()

                # Update catalog metrics (these would be defined in metrics.py)
                # For now, just log the counts
                logger.debug(
                    "Updated catalog metrics",
                    total_products=total_products,
                    total_categories=total_categories,
                )

        except Exception:
            logger.exception("Failed to update catalog metrics")


# Global instance
_background_updater: BackgroundMetricsUpdater | None = None


async def start_background_metrics() -> None:
    """Start the background metrics updater."""
    global _background_updater
    if _background_updater is None:
        _background_updater = BackgroundMetricsUpdater()
    await _background_updater.start()


async def stop_background_metrics() -> None:
    """Stop the background metrics updater."""
    global _background_updater
    if _background_updater:
        await _background_updater.stop()
