from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssetBase(BaseModel):
    name: str
    category: str
    current_price: Decimal


class AssetResponse(AssetBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AssetDetailResponse(AssetResponse):
    price_history: list["PriceHistoryPoint"] = []


class PriceHistoryPoint(BaseModel):
    price: Decimal
    created_at: datetime


class AssetSetPrice(BaseModel):
    price: Decimal


AssetDetailResponse.model_rebuild()
