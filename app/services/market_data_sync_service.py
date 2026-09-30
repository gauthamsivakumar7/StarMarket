from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.price_history import PriceHistory
from app.services.market_data import registry
from app.services.market_data.base import DataAdapterNotSupportedError


async def sync_equity_prices(db: AsyncSession) -> list[Asset]:
    """Mirrors pricing_service.update_prices_simulated's shape, but pulls real
    closes from the resolved market-data adapter instead of a random walk."""
    result = await db.execute(select(Asset).where(Asset.symbol.isnot(None)))
    assets = list(result.scalars().all())

    updated: list[Asset] = []
    for asset in assets:
        try:
            adapter = registry.get_adapter(asset.category)
            latest_price = await adapter.get_latest_price(asset.symbol)
        except (ValueError, DataAdapterNotSupportedError):
            continue
        asset.current_price = latest_price
        db.add(PriceHistory(asset_id=asset.id, price=latest_price))
        updated.append(asset)

    await db.commit()
    for asset in updated:
        await db.refresh(asset)
    return updated
