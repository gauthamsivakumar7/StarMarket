import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import * as strategiesApi from '../api/strategies'
import type { Strategy } from '../types/strategy'
import type { BacktestRun } from '../types/backtest'
import { StatusBadge } from '../components/common/StatusBadge'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { RuleTreeView } from '../components/strategy/RuleTreeView'
import { EquityCurveChart } from '../components/strategy/EquityCurveChart'
import { ExecutionPlanCard } from '../components/strategy/ExecutionPlanCard'
import { SignalRunLogTable } from '../components/strategy/SignalRunLogTable'

type Tab = 'spec' | 'backtests' | 'plans' | 'runs'

export function StrategyDetailPage() {
  const { strategyId } = useParams<{ strategyId: string }>()
  const id = strategyId!
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<Tab>('spec')

  const strategyQuery = useQuery({ queryKey: ['strategy', id], queryFn: () => strategiesApi.getStrategy(id) })
  const backtestsQuery = useQuery({ queryKey: ['strategy', id, 'backtests'], queryFn: () => strategiesApi.listBacktests(id) })
  const plansQuery = useQuery({ queryKey: ['strategy', id, 'plans'], queryFn: () => strategiesApi.listExecutionPlans(id) })
  const runsQuery = useQuery({ queryKey: ['strategy', id, 'runs'], queryFn: () => strategiesApi.listSignalRuns(id) })

  function invalidateStrategy() {
    queryClient.invalidateQueries({ queryKey: ['strategy', id] })
  }

  const resolveMutation = useMutation({ mutationFn: () => strategiesApi.resolveStrategy(id), onSuccess: invalidateStrategy })
  const activateMutation = useMutation({ mutationFn: () => strategiesApi.activateStrategy(id), onSuccess: invalidateStrategy })
  const pauseMutation = useMutation({ mutationFn: () => strategiesApi.pauseStrategy(id), onSuccess: invalidateStrategy })
  const evaluateMutation = useMutation({
    mutationFn: () => strategiesApi.evaluateStrategy(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategy', id, 'runs'] })
      queryClient.invalidateQueries({ queryKey: ['strategy', id, 'plans'] })
      setTab('runs')
    },
  })

  if (strategyQuery.isLoading) return <LoadingSpinner />
  if (strategyQuery.error) return <ErrorBanner error={strategyQuery.error} />
  const strategy = strategyQuery.data
  if (!strategy) return null

  const canActivate = strategy.status === 'backtested' || strategy.status === 'paused'
  const canPause = strategy.status === 'active'
  const canEvaluate = strategy.status !== 'draft' && strategy.status !== 'invalid'

  const actionError = resolveMutation.error || activateMutation.error || pauseMutation.error || evaluateMutation.error

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-semibold text-slate-900">{strategy.name}</h1>
          <StatusBadge status={strategy.status} />
        </div>
        <p className="mt-1 text-sm text-slate-500">{strategy.thesis_text}</p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => resolveMutation.mutate()}
          disabled={resolveMutation.isPending}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
        >
          Resolve instruments
        </button>
        <button
          onClick={() => setTab('backtests')}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          Run backtest
        </button>
        <button
          onClick={() => activateMutation.mutate()}
          disabled={!canActivate || activateMutation.isPending}
          title={!canActivate ? 'Needs a completed backtest first' : undefined}
          className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          Activate
        </button>
        <button
          onClick={() => pauseMutation.mutate()}
          disabled={!canPause || pauseMutation.isPending}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
        >
          Pause
        </button>
        <button
          onClick={() => evaluateMutation.mutate()}
          disabled={!canEvaluate || evaluateMutation.isPending}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
        >
          {evaluateMutation.isPending ? 'Checking signal…' : 'Evaluate now'}
        </button>
      </div>
      {actionError ? <ErrorBanner error={actionError} /> : null}

      <div className="border-b border-slate-200">
        <nav className="-mb-px flex gap-4">
          {(
            [
              ['spec', 'Spec'],
              ['backtests', 'Backtests'],
              ['plans', 'Execution Plans'],
              ['runs', 'Signal Runs'],
            ] as [Tab, string][]
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`border-b-2 px-1 pb-2 text-sm font-medium ${
                tab === key ? 'border-slate-900 text-slate-900' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </div>

      {tab === 'spec' && <SpecTab strategy={strategy} />}
      {tab === 'backtests' && <BacktestsTab strategyId={id} backtests={backtestsQuery.data} isLoading={backtestsQuery.isLoading} />}
      {tab === 'plans' && (
        <div id="execution-plans" className="space-y-3">
          {plansQuery.isLoading && <LoadingSpinner />}
          {plansQuery.data?.length === 0 && <p className="text-sm text-slate-500">No execution plans yet.</p>}
          {plansQuery.data?.map((plan) => (
            <ExecutionPlanCard key={plan.id} plan={plan} strategyId={id} />
          ))}
        </div>
      )}
      {tab === 'runs' && <SignalRunLogTable runs={runsQuery.data ?? []} />}
    </div>
  )
}

function SpecTab({ strategy }: { strategy: Strategy }) {
  const spec = strategy.canonical_spec
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="mb-3 font-medium text-slate-900">Universe</h2>
        <p className="text-sm text-slate-700">{spec.universe.join(', ')} ({spec.asset_class})</p>
        {strategy.resolved_universe && (
          <p className="mt-1 text-xs text-slate-400">
            Resolved: {Object.entries(strategy.resolved_universe).map(([sym, id]) => `${sym} → ${id}`).join(', ')}
          </p>
        )}
        {strategy.context_symbols && strategy.context_symbols.length > 0 && (
          <p className="mt-1 text-xs text-slate-400">Context symbols: {strategy.context_symbols.join(', ')}</p>
        )}
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="mb-3 font-medium text-slate-900">Entry rule</h2>
        <RuleTreeView node={spec.entry_rule} />
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="mb-3 font-medium text-slate-900">Exit rule</h2>
        {spec.exit_rule ? <RuleTreeView node={spec.exit_rule} /> : <p className="text-sm text-slate-400">No exit rule defined.</p>}
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="mb-3 font-medium text-slate-900">Risk &amp; execution</h2>
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-slate-400">Max portfolio risk</dt>
            <dd className="font-medium text-slate-800">{spec.risk.max_portfolio_risk_pct}%</dd>
          </div>
          <div>
            <dt className="text-slate-400">Stop loss</dt>
            <dd className="font-medium text-slate-800">{spec.risk.stop_loss_pct ? `${spec.risk.stop_loss_pct}%` : '—'}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Take profit</dt>
            <dd className="font-medium text-slate-800">{spec.risk.take_profit_pct ? `${spec.risk.take_profit_pct}%` : '—'}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Order type</dt>
            <dd className="font-medium text-slate-800">{spec.execution.order_type}</dd>
          </div>
        </dl>
      </div>

      {strategy.validation_issues && strategy.validation_issues.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="mb-3 font-medium text-slate-900">Validation notes</h2>
          <ul className="space-y-1">
            {strategy.validation_issues.map((issue, i) => (
              <li
                key={i}
                className={`rounded px-2 py-1 text-xs ${
                  issue.severity === 'error' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
                }`}
              >
                {issue.message}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function BacktestsTab({
  strategyId,
  backtests,
  isLoading,
}: {
  strategyId: string
  backtests: BacktestRun[] | undefined
  isLoading: boolean
}) {
  const queryClient = useQueryClient()
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [startingCash, setStartingCash] = useState('10000')

  const mutation = useMutation({
    mutationFn: () =>
      strategiesApi.backtestStrategy(strategyId, {
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        starting_cash: Number(startingCash),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategy', strategyId, 'backtests'] })
      queryClient.invalidateQueries({ queryKey: ['strategy', strategyId] })
    },
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    mutation.mutate()
  }

  const latest = backtests?.[0]

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Start date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="rounded-md border border-slate-300 px-2.5 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">End date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="rounded-md border border-slate-300 px-2.5 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Starting cash</label>
          <input
            type="number"
            min="1"
            value={startingCash}
            onChange={(e) => setStartingCash(e.target.value)}
            className="w-28 rounded-md border border-slate-300 px-2.5 py-1.5 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={mutation.isPending}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {mutation.isPending ? 'Running…' : 'Run backtest'}
        </button>
      </form>
      {mutation.error ? <ErrorBanner error={mutation.error} /> : null}

      {isLoading && <LoadingSpinner />}

      {latest && (
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-medium text-slate-900">Latest run</h2>
            <span className="text-xs text-slate-400">
              {latest.start_date} → {latest.end_date}
            </span>
          </div>

          {latest.status === 'failed' && (
            <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              Backtest failed: {latest.error_message}
            </div>
          )}

          {latest.status === 'completed' && latest.metrics && (
            <>
              <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                <Metric label="Total return" value={`${latest.metrics.total_return_pct.toFixed(2)}%`} />
                <Metric label="Max drawdown" value={`${latest.metrics.max_drawdown_pct.toFixed(2)}%`} />
                <Metric label="Sharpe ratio" value={latest.metrics.sharpe_ratio.toFixed(2)} />
                <Metric label="Win rate" value={`${latest.metrics.win_rate.toFixed(1)}%`} />
                <Metric label="Trades" value={String(latest.metrics.num_trades)} />
                <Metric label="Avg trade return" value={`${latest.metrics.avg_trade_return_pct.toFixed(2)}%`} />
              </div>
              {latest.equity_curve && <EquityCurveChart equityCurve={latest.equity_curve} />}
            </>
          )}
        </div>
      )}

      {backtests && backtests.length > 1 && (
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="mb-3 font-medium text-slate-900">History</h2>
          <ul className="divide-y divide-slate-100 text-sm">
            {backtests.map((b) => (
              <li key={b.id} className="flex items-center justify-between py-2">
                <span className="text-slate-500">
                  {b.start_date} → {b.end_date}
                </span>
                <span className="text-slate-700">
                  {b.status === 'completed' && b.metrics ? `${b.metrics.total_return_pct.toFixed(2)}%` : b.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-slate-400">{label}</p>
      <p className="font-medium text-slate-800">{value}</p>
    </div>
  )
}
