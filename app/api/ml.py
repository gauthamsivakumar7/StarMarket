from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.models.asset import Asset
from app.models.user import User
from app.schemas.ml import ForecastResponse
from app.services.analytics_service import get_forecast_stub

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/assets/{asset_id}/forecast", response_model=ForecastResponse)
async def get_asset_forecast(
    asset_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Asset not found")
    predicted_price, model = await get_forecast_stub(db, asset_id, horizon_days=7)
    return ForecastResponse(
        horizon_days=7,
        predicted_price=predicted_price,
        model=model,
    )
