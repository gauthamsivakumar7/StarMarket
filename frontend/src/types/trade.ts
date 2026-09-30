export interface TradeOrder {
  asset_id: string
  shares: number
}

// TradeResponse.position is a plain dict built with float(...) in trade.py,
// so these are real JSON numbers, unlike the Decimal-typed portfolio/asset fields.
export interface TradePosition {
  asset_id: string
  asset_name: string
  shares: number
  avg_cost: number
}

export interface TradeResponse {
  message: string
  position: TradePosition
  cash_balance: string // Decimal -> JSON string
}
