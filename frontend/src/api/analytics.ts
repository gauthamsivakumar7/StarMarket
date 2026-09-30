import { apiRequest } from './client'
import type { Indicators } from '../types/analytics'

export function getIndicators(assetId: string): Promise<Indicators> {
  return apiRequest<Indicators>(`/analytics/assets/${assetId}/indicators`)
}
