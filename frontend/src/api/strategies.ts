import { apiRequest } from './client'
import type { Strategy } from '../types/strategy'
import type { BacktestRequest, BacktestRun } from '../types/backtest'
import type { ExecutionPlan } from '../types/executionPlan'
import type { SignalRun } from '../types/signalRun'

export function createStrategy(thesisText: string, name?: string): Promise<Strategy> {
  return apiRequest<Strategy>('/strategies', { method: 'POST', body: { thesis_text: thesisText, name } })
}

export function listStrategies(): Promise<Strategy[]> {
  return apiRequest<Strategy[]>('/strategies')
}

export function getStrategy(strategyId: string): Promise<Strategy> {
  return apiRequest<Strategy>(`/strategies/${strategyId}`)
}

export function resolveStrategy(strategyId: string): Promise<Strategy> {
  return apiRequest<Strategy>(`/strategies/${strategyId}/resolve`, { method: 'POST' })
}

export function backtestStrategy(strategyId: string, request: BacktestRequest): Promise<BacktestRun> {
  return apiRequest<BacktestRun>(`/strategies/${strategyId}/backtest`, { method: 'POST', body: request })
}

export function listBacktests(strategyId: string): Promise<BacktestRun[]> {
  return apiRequest<BacktestRun[]>(`/strategies/${strategyId}/backtests`)
}

export function activateStrategy(strategyId: string): Promise<Strategy> {
  return apiRequest<Strategy>(`/strategies/${strategyId}/activate`, { method: 'POST' })
}

export function pauseStrategy(strategyId: string): Promise<Strategy> {
  return apiRequest<Strategy>(`/strategies/${strategyId}/pause`, { method: 'POST' })
}

export function evaluateStrategy(strategyId: string): Promise<SignalRun> {
  return apiRequest<SignalRun>(`/strategies/${strategyId}/evaluate`, { method: 'POST' })
}

export function listExecutionPlans(strategyId: string): Promise<ExecutionPlan[]> {
  return apiRequest<ExecutionPlan[]>(`/strategies/${strategyId}/execution_plans`)
}

export function listSignalRuns(strategyId: string): Promise<SignalRun[]> {
  return apiRequest<SignalRun[]>(`/strategies/${strategyId}/runs`)
}
