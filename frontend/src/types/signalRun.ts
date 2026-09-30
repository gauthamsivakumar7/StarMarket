export type SignalRunTrigger = 'admin_sweep' | 'user_manual'
export type SignalRunAction = 'none' | 'plan_generated' | 'plan_skipped_existing_pending'

export interface SignalSnapshot {
  entry_signal: boolean | null
  exit_signal: boolean | null
  close_prices: Record<string, number>
}

export interface SignalRun {
  id: number
  strategy_id: string
  triggered_by: SignalRunTrigger
  data_asof: string | null
  triggered: boolean
  signal_snapshot: SignalSnapshot | null
  action: SignalRunAction
  execution_plan_id: number | null
  error_message: string | null
  created_at: string | null
}
