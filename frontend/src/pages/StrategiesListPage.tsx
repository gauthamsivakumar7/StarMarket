import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listStrategies } from '../api/strategies'
import { StatusBadge } from '../components/common/StatusBadge'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorBanner } from '../components/common/ErrorBanner'

export function StrategiesListPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ['strategies'], queryFn: listStrategies })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Strategies</h1>
        <Link
          to="/strategies/new"
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
        >
          New strategy
        </Link>
      </div>

      {isLoading && <LoadingSpinner />}
      <ErrorBanner error={error} />

      {data && data.length === 0 && (
        <p className="text-sm text-slate-500">
          No strategies yet. Describe a trading thesis in plain language and StarMarket will turn it into a
          backtestable strategy.
        </p>
      )}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {data?.map((s) => (
          <Link
            key={s.id}
            to={`/strategies/${s.id}`}
            className="rounded-lg border border-slate-200 bg-white p-4 hover:border-slate-300 hover:shadow-sm"
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="font-medium text-slate-900">{s.name}</span>
              <StatusBadge status={s.status} />
            </div>
            <p className="line-clamp-2 text-sm text-slate-500">{s.thesis_text}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
