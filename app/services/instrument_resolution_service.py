from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.price_history import PriceHistory
from app.schemas.strategy_spec import StrategySpec
from app.services.market_data import registry
from app.services.market_data.base import DataAdapterNotSupportedError
from app.services.strategy_compiler_service import collect_symbols


class ResolutionError(Exception):
    pass


async def get_or_create_asset_for_symbol(db: AsyncSession, symbol: str, asset_class: str) -> Asset:
    result = await db.execute(select(Asset).where(Asset.symbol == symbol))
    asset = result.scalar_one_or_none()
    if asset:
        return asset

    if not registry.is_supported(asset_class):
        raise ResolutionError(f"asset_class '{asset_class}' is not yet supported (no data adapter registered)")

    adapter = registry.get_adapter(asset_class)
    try:
        latest_price = await adapter.get_latest_price(symbol)
    except DataAdapterNotSupportedError as e:
        raise ResolutionError(str(e)) from e

    asset = Asset(name=symbol, category=asset_class, symbol=symbol, current_price=latest_price)
    db.add(asset)
    await db.flush()
    db.add(PriceHistory(asset_id=asset.id, price=latest_price))
    return asset


async def resolve_universe(db: AsyncSession, spec: StrategySpec) -> tuple[dict[str, str], list[str]]:
    """Returns (resolved_universe {symbol: asset_id}, context_symbols not in universe)."""
    tradable_symbols = set(spec.universe)
    all_symbols = set(tradable_symbols) | collect_symbols(spec.entry_rule)
    if spec.exit_rule is not None:
        all_symbols |= collect_symbols(spec.exit_rule)

    resolved: dict[str, str] = {}
    for symbol in tradable_symbols:
        asset = await get_or_create_asset_for_symbol(db, symbol, spec.asset_class)
        resolved[symbol] = asset.id

    context_symbols = sorted(all_symbols - tradable_symbols)
    for symbol in context_symbols:
        await get_or_create_asset_for_symbol(db, symbol, spec.asset_class)

    return resolved, context_symbols
