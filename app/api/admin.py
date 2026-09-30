from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db, require_admin
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset import AssetSetPrice
from app.schemas.execution_plan import SignalRunResponse
from app.services import market_data_sync_service, monitoring_service
from app.services.pricing_service import set_asset_price, update_prices_simulated

router = APIRouter(prefix="/admin", tags=["admin"])

ATHLETES = [
    ("LeBron James", 150.0),
    ("Stephen Curry", 120.0),
    ("Kevin Durant", 110.0),
    ("Giannis Antetokounmpo", 140.0),
    ("Luka Doncic", 100.0),
    ("Mike Trout", 85.0),
    ("Shohei Ohtani", 130.0),
    ("Patrick Mahomes", 95.0),
    ("Ja Morant", 75.0),
    ("Nikola Jokic", 115.0),
]


@router.post("/seed")
async def seed_assets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    require_admin(current_user)
    result = await db.execute(select(func.count()).select_from(Asset))
    count = result.scalar() or 0
    if count > 0:
        return {"message": "Database already seeded", "assets_count": count}

    from app.models.price_history import PriceHistory
    for name, price in ATHLETES:
        asset = Asset(name=name, category="athlete", current_price=price)
        db.add(asset)
    await db.flush()
    result = await db.execute(select(Asset))
    for asset in result.scalars().all():
        ph = PriceHistory(asset_id=asset.id, price=asset.current_price)
        db.add(ph)
    await db.commit()

    result = await db.execute(select(func.count()).select_from(Asset))
    return {"message": "Seeded athletes", "assets_count": result.scalar()}


@router.post("/assets/{asset_id}/set_price")
async def admin_set_price(
    asset_id: str,
    body: AssetSetPrice,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    require_admin(current_user)
    asset = await set_asset_price(db, asset_id, body.price)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"message": "Price updated", "asset_id": asset_id, "price": float(asset.current_price)}


@router.post("/assets/update_prices_simulated")
async def admin_update_prices_simulated(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    require_admin(current_user)
    assets = await update_prices_simulated(db)
    return {
        "message": "Prices updated (random walk)",
        "assets_updated": len(assets),
        "prices": {a.id: float(a.current_price) for a in assets},
    }


@router.post("/market-data/sync")
async def admin_sync_market_data(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    require_admin(current_user)
    assets = await market_data_sync_service.sync_equity_prices(db)
    return {
        "message": "Synced equity prices from live market data",
        "assets_updated": len(assets),
        "prices": {a.id: float(a.current_price) for a in assets},
    }


@router.post("/strategies/monitoring/run", response_model=list[SignalRunResponse])
async def admin_run_monitoring_sweep(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    require_admin(current_user)
    return await monitoring_service.run_monitoring_sweep(db)
