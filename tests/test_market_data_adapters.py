from datetime import date

import pytest

from app.services.market_data import registry
from app.services.market_data.base import DataAdapterNotSupportedError
from app.services.market_data.equity_adapter import YFinanceEquityAdapter
from app.services.market_data.stub_adapters import (
    CommodityAdapter,
    CryptoAdapter,
    PredictionMarketAdapter,
    YieldAdapter,
)

STUB_ADAPTERS = [CryptoAdapter(), PredictionMarketAdapter(), CommodityAdapter(), YieldAdapter()]


@pytest.mark.parametrize("adapter", STUB_ADAPTERS)
async def test_stub_adapters_raise_on_get_ohlcv(adapter):
    with pytest.raises(DataAdapterNotSupportedError, match="not yet implemented"):
        await adapter.get_ohlcv("BTC-USD", date(2024, 1, 1), date(2024, 1, 2))


@pytest.mark.parametrize("adapter", STUB_ADAPTERS)
async def test_stub_adapters_raise_on_get_latest_price(adapter):
    with pytest.raises(DataAdapterNotSupportedError, match="not yet implemented"):
        await adapter.get_latest_price("BTC-USD")


def test_registry_wiring():
    assert isinstance(registry.get_adapter("equity"), YFinanceEquityAdapter)
    assert isinstance(registry.get_adapter("crypto"), CryptoAdapter)
    assert isinstance(registry.get_adapter("prediction_market"), PredictionMarketAdapter)
    assert isinstance(registry.get_adapter("commodity"), CommodityAdapter)
    assert isinstance(registry.get_adapter("yield"), YieldAdapter)


def test_only_equity_is_supported_today():
    assert registry.is_supported("equity") is True
    for asset_class in ("crypto", "prediction_market", "commodity", "yield"):
        assert registry.is_supported(asset_class) is False
