export interface PortfolioPosition {
  asset_id: string
  asset_name: string
  shares: string // Decimal -> JSON string
  avg_cost: string
  current_price: string
  market_value: string
  cost_basis: string
  unrealized_pnl: string
  unrealized_pnl_pct: string | null
}

export interface Portfolio {
  holdings: PortfolioPosition[]
  total_market_value: string
  total_cost_basis: string
  total_unrealized_pnl: string
  total_unrealized_pnl_pct: string | null
}
