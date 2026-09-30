import { SimpleLineChart } from '../common/SimpleLineChart'
import type { PriceHistoryPoint } from '../../types/asset'

export function AssetPriceChart({ priceHistory }: { priceHistory: PriceHistoryPoint[] }) {
  const points = priceHistory.map((p) => ({ x: p.created_at, y: Number(p.price) }))
  return (
    <SimpleLineChart
      points={points}
      formatValue={(v) => `$${v.toFixed(2)}`}
      formatDate={(x) => new Date(x).toLocaleDateString()}
    />
  )
}
