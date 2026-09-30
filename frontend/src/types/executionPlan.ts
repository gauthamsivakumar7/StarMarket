export type PlanStatus =
  | 'pending_approval'
  | 'approved'
  | 'rejected'
  | 'expired'
  | 'executed'
  | 'failed'
  | 'partially_filled'

export type PlanTrigger = 'user_manual' | 'monitoring_sweep'

// proposed_orders/risk_assessment/fills are JSONB dicts on the backend, built
// with float(...)/native types in execution_plan_service.py — real JSON numbers.
export interface ProposedOrder {
  symbol: string
  asset_id: string
  side: 'BUY' | 'SELL'
  order_type: 'MARKET'
  shares: number
  estimated_price: number
  estimated_cost: number
  rationale: string
}

export interface RiskAssessment {
  passed: boolean
  blocking_issues: string[]
  warnings: string[]
  checked_at: string
}

export interface Fill {
  order_index: number
  status: 'filled' | 'failed'
  price_per_share: number | null
  shares: number | null
  total_value: number | null
  filled_at: string
  error_message: string | null
}

export interface ExecutionPlan {
  id: number
  strategy_id: string
  backtest_run_id: number
  status: PlanStatus
  triggered_by: PlanTrigger
  proposed_orders: ProposedOrder[]
  risk_assessment: RiskAssessment
  approval_risk_recheck: RiskAssessment | null
  fills: Fill[] | null
  created_at: string | null
  expires_at: string
  approved_at: string | null
  rejected_at: string | null
  executed_at: string | null
}
