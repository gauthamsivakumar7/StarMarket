import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { getAsset } from '../api/assets'
import { getIndicators } from '../api/analytics'
import { getForecast } from '../api/ml'
import { Money } from '../components/common/Money'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { AssetPriceChart } from '../components/trading/AssetPriceChart'
import { TradeForm } from '../components/trading/TradeForm'

function formatPct(value: string | null): string {
  if (value === null) return '—'
  return `${(Number(value) * 100).toFixed(2)}%`
}

export function AssetDetailPage() {
  const { assetId } = useParams<{ assetId: string }>()
  const assetQuery = useQuery({ queryKey: ['asset', assetId], queryFn: () => getAsset(assetId!), enabled: !!assetId })
  const indicatorsQuery = useQuery({
    queryKey: ['indicators', assetId],
    queryFn: () => getIndicators(assetId!),
    enabled: !!assetId,
  })
  const forecastQuery = useQuery({
    queryKey: ['forecast', assetId],
    queryFn: () => getForecast(assetId!),
    enabled: !!assetId,
  })

  if (assetQuery.isLoading) return <LoadingSpinner />
  if (assetQuery.error) return <ErrorBanner error={assetQuery.error} />
  const asset = assetQuery.data
  if (!asset) return null

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-wide text-slate-400">{asset.category}</p>
        <h1 className="text-2xl font-semibold text-slate-900">{asset.name}</h1>
        <p className="mt-1 text-3xl font-semibold text-slate-900">
          <Money value={asset.current_price} />
        </p>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="mb-3 font-medium text-slate-900">Price history</h2>
        <AssetPriceChart priceHistory={asset.price_history} />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="mb-3 font-medium text-slate-900">Indicators</h2>
          {indicatorsQuery.isLoading && <LoadingSpinner />}
          {indicatorsQuery.data && (
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-slate-400">7-day mean</dt>
                <dd className="font-medium text-slate-800">
                  {indicatorsQuery.data.rolling_mean_7 ? <Money value={indicatorsQuery.data.rolling_mean_7} /> : '—'}
                </dd>
              </div>
              <div>
                <dt className="text-slate-400">30-day mean</dt>
                <dd className="font-medium text-slate-800">
                  {indicatorsQuery.data.rolling_mean_30 ? <Money value={indicatorsQuery.data.rolling_mean_30} /> : '—'}
                </dd>
              </div>
              <div>
                <dt className="text-slate-400">Volatility</dt>
                <dd className="font-medium text-slate-800">{formatPct(indicatorsQuery.data.volatility)}</dd>
              </div>
              <div>
                <dt className="text-slate-400">Momentum</dt>
                <dd className="font-medium text-slate-800">{formatPct(indicatorsQuery.data.momentum_pct)}</dd>
              </div>
            </dl>
          )}
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="mb-3 font-medium text-slate-900">Forecast (stub model)</h2>
          {forecastQuery.data && (
            <p className="text-sm text-slate-600">
              Projected in {forecastQuery.data.horizon_days} days:{' '}
              <span className="font-semibold text-slate-900">
                <Money value={forecastQuery.data.predicted_price} />
              </span>{' '}
              <span className="text-xs text-slate-400">({forecastQuery.data.model})</span>
            </p>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="mb-3 font-medium text-slate-900">Buy shares</h2>
        <TradeForm assetId={asset.id} side="BUY" />
      </div>
    </div>
  )
}
