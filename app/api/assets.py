from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_active_user, get_db
from app.models.asset import Asset
from app.models.price_history import PriceHistory
from app.models.user import User
from app.schemas.asset import AssetDetailResponse, AssetResponse, PriceHistoryPoint

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=list[AssetResponse])
async def list_assets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(select(Asset).order_by(Asset.name))
    assets = result.scalars().all()
    return list(assets)


@router.get("/{asset_id}", response_model=AssetDetailResponse)
async def get_asset(
    asset_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(30, ge=1, le=100),
):
    result = await db.execute(
        select(Asset)
        .where(Asset.id == asset_id)
        .options(selectinload(Asset.price_history))
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    ph_result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.asset_id == asset_id)
        .order_by(PriceHistory.created_at.desc())
        .limit(limit)
    )
    history = list(reversed(ph_result.scalars().all()))

    return AssetDetailResponse(
        id=asset.id,
        name=asset.name,
        category=asset.category,
        current_price=asset.current_price,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        price_history=[PriceHistoryPoint(price=h.price, created_at=h.created_at) for h in history],
    )
