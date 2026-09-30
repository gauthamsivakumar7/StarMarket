from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.models.asset import Asset
from app.models.user import User
from app.schemas.analytics import IndicatorsResponse
from app.services.analytics_service import get_indicators

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/assets/{asset_id}/indicators", response_model=IndicatorsResponse)
async def get_asset_indicators(
    asset_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Asset not found")
    data = await get_indicators(db, asset_id)
    return IndicatorsResponse(**data)
