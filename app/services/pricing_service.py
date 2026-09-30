import random
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.price_history import PriceHistory


async def set_asset_price(
    db: AsyncSession, asset_id: str, price: Decimal
) -> Asset | None:
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        return None
    asset.current_price = price
    ph = PriceHistory(asset_id=asset_id, price=price)
    db.add(ph)
    await db.commit()
    await db.refresh(asset)
    return asset


async def update_prices_simulated(db: AsyncSession) -> list[Asset]:
    result = await db.execute(select(Asset))
    assets = list(result.scalars().all())
    for asset in assets:
        factor = Decimal(str(1 + random.uniform(-0.05, 0.05)))
        new_price = (asset.current_price * factor).quantize(Decimal("0.000001"))
        if new_price <= 0:
            new_price = Decimal("0.01")
        asset.current_price = new_price
        ph = PriceHistory(asset_id=asset.id, price=new_price)
        db.add(ph)
    await db.commit()
    for asset in assets:
        await db.refresh(asset)
    return assets
