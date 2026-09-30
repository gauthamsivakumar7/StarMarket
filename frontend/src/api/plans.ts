import { apiRequest } from './client'
import type { ExecutionPlan } from '../types/executionPlan'

export function getPlan(planId: number): Promise<ExecutionPlan> {
  return apiRequest<ExecutionPlan>(`/plans/${planId}`)
}

export function approvePlan(planId: number): Promise<ExecutionPlan> {
  return apiRequest<ExecutionPlan>(`/plans/${planId}/approve`, { method: 'POST' })
}

export function rejectPlan(planId: number): Promise<ExecutionPlan> {
  return apiRequest<ExecutionPlan>(`/plans/${planId}/reject`, { method: 'POST' })
}
