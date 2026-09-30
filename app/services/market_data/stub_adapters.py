from datetime import date
from decimal import Decimal

from app.services.market_data.base import DataAdapterNotSupportedError, MarketDataAdapter


class _NotYetSupportedAdapter(MarketDataAdapter):
    """Base for asset classes deferred out of v1 scope. Raises a clear error
    instead of fabricating data. To add real support: implement get_ohlcv and
    get_latest_price in a new adapter class and register it in registry.py."""

    asset_class: str = "unknown"

    async def get_ohlcv(self, symbol: str, start: date, end: date) -> list:
        raise DataAdapterNotSupportedError(
            f"{self.asset_class} data adapter not yet implemented; implement get_ohlcv "
            f"in app/services/market_data/{self.asset_class}_adapter.py and register it "
            f"in app/services/market_data/registry.py"
        )

    async def get_latest_price(self, symbol: str) -> Decimal:
        raise DataAdapterNotSupportedError(
            f"{self.asset_class} data adapter not yet implemented; implement get_latest_price "
            f"in app/services/market_data/{self.asset_class}_adapter.py and register it "
            f"in app/services/market_data/registry.py"
        )


class CryptoAdapter(_NotYetSupportedAdapter):
    asset_class = "crypto"


class PredictionMarketAdapter(_NotYetSupportedAdapter):
    asset_class = "prediction_market"


class CommodityAdapter(_NotYetSupportedAdapter):
    asset_class = "commodity"


class YieldAdapter(_NotYetSupportedAdapter):
    asset_class = "yield"
