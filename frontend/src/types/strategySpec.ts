export type IndicatorName = 'SMA' | 'EMA' | 'RSI' | 'CLOSE' | 'VOLUME'
export type ComparisonOp = 'crosses_above' | 'crosses_below' | '>' | '<' | '>=' | '<=' | '=='
export type AssetClass = 'equity' | 'crypto' | 'prediction_market' | 'commodity' | 'yield'

export interface Constant {
  type: 'constant'
  value: string // Decimal -> JSON string
}

export interface IndicatorRef {
  type: 'indicator'
  name: IndicatorName
  symbol: string
  params: Record<string, number>
}

export type Operand = IndicatorRef | Constant

export interface Condition {
  type: 'condition'
  left: Operand
  op: ComparisonOp
  right: Operand
}

export interface BooleanOp {
  type: 'and' | 'or' | 'not'
  children: RuleNode[]
}

export type RuleNode = Condition | BooleanOp

export interface RiskParams {
  max_portfolio_risk_pct: string
  stop_loss_pct: string | null
  take_profit_pct: string | null
  max_position_pct: string
}

export interface ExecutionParams {
  order_type: 'MARKET'
}

export interface StrategySpec {
  name: string
  universe: string[]
  asset_class: AssetClass
  entry_rule: RuleNode
  exit_rule: RuleNode | null
  risk: RiskParams
  execution: ExecutionParams
  timeframe: '1d'
}
