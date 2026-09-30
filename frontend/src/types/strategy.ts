import type { StrategySpec } from './strategySpec'

export type StrategyStatus = 'draft' | 'invalid' | 'resolved' | 'backtested' | 'active' | 'paused' | 'archived'

export interface ValidationIssue {
  severity: 'error' | 'warning'
  code: string
  message: string
}

export interface Strategy {
  id: string
  name: string
  thesis_text: string
  asset_class: string
  canonical_spec: StrategySpec
  validation_issues: ValidationIssue[] | null
  resolved_universe: Record<string, string> | null
  context_symbols: string[] | null
  status: StrategyStatus
  created_at: string | null
  updated_at: string | null
}
