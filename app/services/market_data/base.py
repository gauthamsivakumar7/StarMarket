from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class OHLCVBar(BaseModel):
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class DataAdapterNotSupportedError(Exception):
    pass


class MarketDataAdapter(ABC):
    @abstractmethod
    async def get_ohlcv(self, symbol: str, start: date, end: date) -> list[OHLCVBar]: ...

    @abstractmethod
    async def get_latest_price(self, symbol: str) -> Decimal: ...
