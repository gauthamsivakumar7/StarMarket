from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StrategyCreateRequest(BaseModel):
    thesis_text: str
    name: str | None = None


class StrategyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    thesis_text: str
    asset_class: str
    canonical_spec: dict
    validation_issues: list[dict] | None = None
    resolved_universe: dict | None = None
    context_symbols: list[str] | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
