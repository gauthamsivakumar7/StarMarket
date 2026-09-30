import asyncio
import time
from datetime import date
from decimal import Decimal
from typing import Any

from app.core.config import get_settings
from app.services.market_data.base import MarketDataAdapter, OHLCVBar


class YFinanceEquityAdapter(MarketDataAdapter):
    """Real equity/index data via yfinance. The only I/O boundary where a
    pandas DataFrame exists in this codebase — converted to OHLCVBar here and
    never passed further downstream."""

    def __init__(self) -> None:
        self._cache: dict[tuple, tuple[float, list[OHLCVBar]]] = {}

    async def get_ohlcv(self, symbol: str, start: date, end: date) -> list[OHLCVBar]:
        cache_key = (symbol, start, end)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        bars = await asyncio.to_thread(self._fetch_ohlcv_sync, symbol, start, end)
        self._cache_set(cache_key, bars)
        return bars

    async def get_latest_price(self, symbol: str) -> Decimal:
        bars = await asyncio.to_thread(self._fetch_recent_sync, symbol)
        if not bars:
            raise ValueError(f"No price data available for symbol '{symbol}'")
        return bars[-1].close

    def _cache_get(self, key: tuple) -> list[OHLCVBar] | None:
        settings = get_settings()
        entry = self._cache.get(key)
        if entry is None:
            return None
        cached_at, bars = entry
        if time.monotonic() - cached_at > settings.market_data_cache_ttl_seconds:
            return None
        return bars

    def _cache_set(self, key: tuple, bars: list[OHLCVBar]) -> None:
        self._cache[key] = (time.monotonic(), bars)

    def _fetch_ohlcv_sync(self, symbol: str, start: date, end: date) -> list[OHLCVBar]:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, interval="1d")
        return self._dataframe_to_bars(df)

    def _fetch_recent_sync(self, symbol: str) -> list[OHLCVBar]:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="1d")
        return self._dataframe_to_bars(df)

    @staticmethod
    def _dataframe_to_bars(df: Any) -> list[OHLCVBar]:
        bars: list[OHLCVBar] = []
        for idx, row in df.iterrows():
            bars.append(
                OHLCVBar(
                    date=idx.date() if hasattr(idx, "date") else idx,
                    open=Decimal(str(row["Open"])),
                    high=Decimal(str(row["High"])),
                    low=Decimal(str(row["Low"])),
                    close=Decimal(str(row["Close"])),
                    volume=int(row["Volume"]),
                )
            )
        return bars
