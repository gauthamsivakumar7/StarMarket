import { apiRequest } from './client'
import type { SignalRun } from '../types/signalRun'

interface SeedResult {
  message: string
  assets_count: number
}

interface PriceUpdateResult {
  message: string
  assets_updated: number
  prices: Record<string, number>
}

export function seedAssets(): Promise<SeedResult> {
  return apiRequest<SeedResult>('/admin/seed', { method: 'POST' })
}

export function updatePricesSimulated(): Promise<PriceUpdateResult> {
  return apiRequest<PriceUpdateResult>('/admin/assets/update_prices_simulated', { method: 'POST' })
}

export function syncMarketData(): Promise<PriceUpdateResult> {
  return apiRequest<PriceUpdateResult>('/admin/market-data/sync', { method: 'POST' })
}

export function runMonitoringSweep(): Promise<SignalRun[]> {
  return apiRequest<SignalRun[]>('/admin/strategies/monitoring/run', { method: 'POST' })
}
