from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExecutionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    strategy_id: str
    backtest_run_id: int
    status: str
    triggered_by: str
    proposed_orders: list[dict]
    risk_assessment: dict
    approval_risk_recheck: dict | None = None
    fills: list[dict] | None = None
    created_at: datetime | None = None
    expires_at: datetime
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    executed_at: datetime | None = None


class SignalRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    strategy_id: str
    triggered_by: str
    data_asof: datetime | None = None
    triggered: bool
    signal_snapshot: dict | None = None
    action: str
    execution_plan_id: int | None = None
    error_message: str | None = None
    created_at: datetime | None = None
