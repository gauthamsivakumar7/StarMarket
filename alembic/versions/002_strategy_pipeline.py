"""Strategy pipeline: NL strategies, backtests, execution plans, signal runs

Revision ID: 002
Revises: 001
Create Date: 2026-09-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("symbol", sa.String(50), nullable=True))
    op.create_index("ix_assets_symbol", "assets", ["symbol"], unique=True)

    op.create_table(
        "strategies",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("thesis_text", sa.Text(), nullable=False),
        sa.Column("asset_class", sa.String(50), nullable=False),
        sa.Column("canonical_spec", postgresql.JSONB(), nullable=False),
        sa.Column("validation_issues", postgresql.JSONB(), nullable=True),
        sa.Column("resolved_universe", postgresql.JSONB(), nullable=True),
        sa.Column("context_symbols", postgresql.JSONB(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "invalid", "resolved", "backtested", "active", "paused", "archived",
                name="strategystatus",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_strategies_user_id", "strategies", ["user_id"])

    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="backteststatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("starting_cash", sa.Numeric(18, 6), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), nullable=True),
        sa.Column("equity_curve", postgresql.JSONB(), nullable=True),
        sa.Column("trades", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_backtest_runs_strategy_id", "backtest_runs", ["strategy_id"])

    op.create_table(
        "execution_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("backtest_run_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending_approval", "approved", "rejected", "expired", "executed",
                "failed", "partially_filled",
                name="executionplanstatus",
            ),
            nullable=False,
            server_default="pending_approval",
        ),
        sa.Column(
            "triggered_by",
            sa.Enum("user_manual", "monitoring_sweep", name="executionplantrigger"),
            nullable=False,
        ),
        sa.Column("proposed_orders", postgresql.JSONB(), nullable=False),
        sa.Column("risk_assessment", postgresql.JSONB(), nullable=False),
        sa.Column("approval_risk_recheck", postgresql.JSONB(), nullable=True),
        sa.Column("fills", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_execution_plans_strategy_id", "execution_plans", ["strategy_id"])

    op.create_table(
        "strategy_signal_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "triggered_by",
            sa.Enum("admin_sweep", "user_manual", name="signalruntrigger"),
            nullable=False,
        ),
        sa.Column("data_asof", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("signal_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column(
            "action",
            sa.Enum(
                "none", "plan_generated", "plan_skipped_existing_pending", name="signalrunaction"
            ),
            nullable=False,
            server_default="none",
        ),
        sa.Column("execution_plan_id", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["execution_plan_id"], ["execution_plans.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_strategy_signal_runs_strategy_id", "strategy_signal_runs", ["strategy_id"])


def downgrade() -> None:
    op.drop_index("ix_strategy_signal_runs_strategy_id", table_name="strategy_signal_runs")
    op.drop_table("strategy_signal_runs")
    op.execute("DROP TYPE IF EXISTS signalrunaction")
    op.execute("DROP TYPE IF EXISTS signalruntrigger")

    op.drop_index("ix_execution_plans_strategy_id", table_name="execution_plans")
    op.drop_table("execution_plans")
    op.execute("DROP TYPE IF EXISTS executionplantrigger")
    op.execute("DROP TYPE IF EXISTS executionplanstatus")

    op.drop_index("ix_backtest_runs_strategy_id", table_name="backtest_runs")
    op.drop_table("backtest_runs")
    op.execute("DROP TYPE IF EXISTS backteststatus")

    op.drop_index("ix_strategies_user_id", table_name="strategies")
    op.drop_table("strategies")
    op.execute("DROP TYPE IF EXISTS strategystatus")

    op.drop_index("ix_assets_symbol", table_name="assets")
    op.drop_column("assets", "symbol")
