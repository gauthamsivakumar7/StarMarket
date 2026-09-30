import { apiRequest } from './client'
import type { TradeOrder, TradeResponse } from '../types/trade'

export function buy(order: TradeOrder): Promise<TradeResponse> {
  return apiRequest<TradeResponse>('/trade/buy', {
    method: 'POST',
    body: order,
    headers: { 'Idempotency-Key': crypto.randomUUID() },
  })
}

export function sell(order: TradeOrder): Promise<TradeResponse> {
  return apiRequest<TradeResponse>('/trade/sell', {
    method: 'POST',
    body: order,
    headers: { 'Idempotency-Key': crypto.randomUUID() },
  })
}
