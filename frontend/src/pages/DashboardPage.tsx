import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getPortfolio } from '../api/portfolio'
import { listStrategies } from '../api/strategies'
import { useAuth } from '../context/AuthContext'
import { Money } from '../components/common/Money'
import { StatusBadge } from '../components/common/StatusBadge'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorBanner } from '../components/common/ErrorBanner'

export function DashboardPage() {
  const { user } = useAuth()
  const portfolioQuery = useQuery({ queryKey: ['portfolio'], queryFn: getPortfolio })
  const strategiesQuery = useQuery({ queryKey: ['strategies'], queryFn: listStrategies })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500">Welcome back, {user?.username || user?.email}.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Cash balance</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">
            {user && <Money value={user.cash_balance} />}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Portfolio value</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">
            {portfolioQuery.data && <Money value={portfolioQuery.data.total_market_value} />}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Unrealized PnL</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">
            {portfolioQuery.data ? (
              <Money value={portfolioQuery.data.total_unrealized_pnl} />
            ) : (
              '—'
            )}
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-medium text-slate-900">Your strategies</h2>
          <Link
            to="/strategies/new"
            className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
          >
            New strategy
          </Link>
        </div>
        {strategiesQuery.isLoading && <LoadingSpinner />}
        <ErrorBanner error={strategiesQuery.error} />
        {strategiesQuery.data && strategiesQuery.data.length === 0 && (
          <p className="text-sm text-slate-500">
            No strategies yet. Describe a trading thesis in plain language to get started.
          </p>
        )}
        <ul className="divide-y divide-slate-100">
          {strategiesQuery.data?.slice(0, 5).map((s) => (
            <li key={s.id} className="flex items-center justify-between py-3">
              <Link to={`/strategies/${s.id}`} className="font-medium text-slate-800 hover:underline">
                {s.name}
              </Link>
              <StatusBadge status={s.status} />
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
