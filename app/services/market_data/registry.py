from app.services.market_data.base import MarketDataAdapter
from app.services.market_data.equity_adapter import YFinanceEquityAdapter
from app.services.market_data.stub_adapters import (
    CommodityAdapter,
    CryptoAdapter,
    PredictionMarketAdapter,
    YieldAdapter,
)

_ADAPTERS: dict[str, MarketDataAdapter] = {
    "equity": YFinanceEquityAdapter(),
    "crypto": CryptoAdapter(),
    "prediction_market": PredictionMarketAdapter(),
    "commodity": CommodityAdapter(),
    "yield": YieldAdapter(),
}

SUPPORTED_ASSET_CLASSES = {"equity"}


def is_supported(asset_class: str) -> bool:
    return asset_class in SUPPORTED_ASSET_CLASSES


def get_adapter(asset_class: str) -> MarketDataAdapter:
    adapter = _ADAPTERS.get(asset_class)
    if adapter is None:
        raise ValueError(f"No market data adapter registered for asset_class '{asset_class}'")
    return adapter
