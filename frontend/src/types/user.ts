export interface User {
  id: string
  email: string
  username: string | null
  is_admin: boolean
  cash_balance: string // Decimal -> JSON string
  created_at: string | null
}
