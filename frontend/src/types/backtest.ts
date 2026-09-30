export type BacktestStatus = 'pending' | 'running' | 'completed' | 'failed'
export type ExitReason = 'stop_loss' | 'take_profit' | 'exit_rule' | 'backtest_end'

// These are already plain numbers in JSON — the backend service code calls
// float(...) before storing them in the JSONB column (see backtest_service.py).
export interface BacktestMetrics {
  total_return_pct: number
  max_drawdown_pct: number
  sharpe_ratio: number
  win_rate: number
  num_trades: number
  avg_trade_return_pct: number
}

export interface EquityPoint {
  date: string
  equity: number
}

export interface BacktestTrade {
  entry_date: string
  entry_price: number
  exit_date: string
  exit_price: number
  shares: number
  return_pct: number
  exit_reason: ExitReason
}

export interface BacktestRun {
  id: number
  strategy_id: string
  status: BacktestStatus
  start_date: string
  end_date: string
  starting_cash: string // Decimal -> JSON string
  metrics: BacktestMetrics | null
  equity_curve: EquityPoint[] | null
  trades: BacktestTrade[] | null
  error_message: string | null
  created_at: string | null
  completed_at: string | null
}

export interface BacktestRequest {
  start_date?: string
  end_date?: string
  starting_cash?: number
}
