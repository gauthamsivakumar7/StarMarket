export interface Asset {
  id: string
  name: string
  category: string
  current_price: string // Decimal -> JSON string
  created_at: string | null
  updated_at: string | null
}

export interface PriceHistoryPoint {
  price: string // Decimal -> JSON string
  created_at: string
}

export interface AssetDetail extends Asset {
  price_history: PriceHistoryPoint[]
}
