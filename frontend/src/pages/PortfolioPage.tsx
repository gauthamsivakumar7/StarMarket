import { useQuery } from '@tanstack/react-query'
import { getPortfolio } from '../api/portfolio'
import { Money } from '../components/common/Money'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { PortfolioTable } from '../components/trading/PortfolioTable'

export function PortfolioPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ['portfolio'], queryFn: getPortfolio })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">Portfolio</h1>

      {isLoading && <LoadingSpinner />}
      <ErrorBanner error={error} />

      {data && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Market value</p>
              <p className="mt-1 text-xl font-semibold text-slate-900">
                <Money value={data.total_market_value} />
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Cost basis</p>
              <p className="mt-1 text-xl font-semibold text-slate-900">
                <Money value={data.total_cost_basis} />
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Unrealized PnL</p>
              <p className="mt-1 text-xl font-semibold text-slate-900">
                <Money value={data.total_unrealized_pnl} />
                {data.total_unrealized_pnl_pct !== null && (
                  <span className="ml-1 text-sm text-slate-400">
                    ({Number(data.total_unrealized_pnl_pct).toFixed(1)}%)
                  </span>
                )}
              </p>
            </div>
          </div>

          <PortfolioTable holdings={data.holdings} />
        </>
      )}
    </div>
  )
}
