import { SimpleLineChart } from '../common/SimpleLineChart'
import type { EquityPoint } from '../../types/backtest'

export function EquityCurveChart({ equityCurve }: { equityCurve: EquityPoint[] }) {
  const points = equityCurve.map((p) => ({ x: p.date, y: p.equity }))
  return (
    <SimpleLineChart
      points={points}
      formatValue={(v) => `$${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
      formatDate={(x) => new Date(x).toLocaleDateString()}
    />
  )
}
