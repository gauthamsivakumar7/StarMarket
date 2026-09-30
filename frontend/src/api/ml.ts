import { apiRequest } from './client'
import type { Forecast } from '../types/ml'

export function getForecast(assetId: string): Promise<Forecast> {
  return apiRequest<Forecast>(`/ml/assets/${assetId}/forecast`)
}
