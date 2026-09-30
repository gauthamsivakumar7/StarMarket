import { apiRequest } from './client'
import type { Portfolio } from '../types/portfolio'

export function getPortfolio(): Promise<Portfolio> {
  return apiRequest<Portfolio>('/portfolio')
}
