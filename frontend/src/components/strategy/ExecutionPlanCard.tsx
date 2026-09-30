import { useMutation, useQueryClient } from '@tanstack/react-query'
import * as plansApi from '../../api/plans'
import type { ExecutionPlan } from '../../types/executionPlan'
import { StatusBadge } from '../common/StatusBadge'
import { ErrorBanner } from '../common/ErrorBanner'
import { Money } from '../common/Money'
import { RiskAssessmentCard } from './RiskAssessmentCard'

export function ExecutionPlanCard({ plan, strategyId }: { plan: ExecutionPlan; strategyId: string }) {
  const queryClient = useQueryClient()

  function invalidateAfterAction() {
    queryClient.invalidateQueries({ queryKey: ['strategy', strategyId, 'plans'] })
    queryClient.invalidateQueries({ queryKey: ['portfolio'] })
    queryClient.invalidateQueries({ queryKey: ['me'] })
  }

  const approveMutation = useMutation({
    mutationFn: () => plansApi.approvePlan(plan.id),
    onSuccess: invalidateAfterAction,
  })
  const rejectMutation = useMutation({
    mutationFn: () => plansApi.rejectPlan(plan.id),
    onSuccess: invalidateAfterAction,
  })

  const isPending = plan.status === 'pending_approval'

  return (
    <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <div className="text-xs text-slate-400">
          Plan #{plan.id} · {plan.triggered_by.replace('_', ' ')} · created{' '}
          {plan.created_at ? new Date(plan.created_at).toLocaleString() : ''}
        </div>
        <StatusBadge status={plan.status} />
      </div>

      <div className="space-y-1.5">
        {plan.proposed_orders.map((order, i) => (
          <div key={i} className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 text-sm">
            <span className="font-medium text-slate-800">
              {order.side} {order.shares} {order.symbol}
            </span>
            <span className="text-slate-500">
              est. <Money value={order.estimated_cost || order.estimated_price * order.shares} />
            </span>
          </div>
        ))}
      </div>

      <RiskAssessmentCard assessment={plan.risk_assessment} title="Risk assessment (at generation)" />
      {plan.approval_risk_recheck && (
        <RiskAssessmentCard assessment={plan.approval_risk_recheck} title="Risk re-check (at approval)" />
      )}

      {plan.fills && plan.fills.length > 0 && (
        <div className="space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Fills</span>
          {plan.fills.map((fill) => (
            <div key={fill.order_index} className="flex items-center justify-between text-sm">
              <span className={fill.status === 'filled' ? 'text-emerald-600' : 'text-red-600'}>{fill.status}</span>
              {fill.price_per_share !== null && (
                <span className="text-slate-500">
                  {fill.shares} @ <Money value={fill.price_per_share} />
                </span>
              )}
              {fill.error_message && <span className="text-red-600">{fill.error_message}</span>}
            </div>
          ))}
        </div>
      )}

      {isPending && (
        <div className="flex items-center gap-2 pt-1">
          <button
            onClick={() => approveMutation.mutate()}
            disabled={approveMutation.isPending || rejectMutation.isPending}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            Approve &amp; execute
          </button>
          <button
            onClick={() => rejectMutation.mutate()}
            disabled={approveMutation.isPending || rejectMutation.isPending}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
          >
            Reject
          </button>
        </div>
      )}
      <ErrorBanner error={approveMutation.error || rejectMutation.error} />
    </div>
  )
}
