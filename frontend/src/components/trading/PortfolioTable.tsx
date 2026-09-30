import { Fragment, useState } from 'react'
import { Link } from 'react-router-dom'
import type { PortfolioPosition } from '../../types/portfolio'
import { Money } from '../common/Money'
import { TradeForm } from './TradeForm'

function pnlColor(pnl: string): string {
  return Number(pnl) >= 0 ? 'text-emerald-600' : 'text-red-600'
}

export function PortfolioTable({ holdings }: { holdings: PortfolioPosition[] }) {
  const [sellingAssetId, setSellingAssetId] = useState<string | null>(null)

  if (holdings.length === 0) {
    return <p className="text-sm text-slate-500">No holdings yet — buy something from the Assets page.</p>
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="border-b border-slate-100 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-400">
          <tr>
            <th className="px-4 py-2 font-medium">Asset</th>
            <th className="px-4 py-2 font-medium text-right">Shares</th>
            <th className="px-4 py-2 font-medium text-right">Avg cost</th>
            <th className="px-4 py-2 font-medium text-right">Market value</th>
            <th className="px-4 py-2 font-medium text-right">Unrealized PnL</th>
            <th className="px-4 py-2 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {holdings.map((h) => (
            <Fragment key={h.asset_id}>
              <tr className="hover:bg-slate-50">
                <td className="px-4 py-2.5">
                  <Link to={`/assets/${h.asset_id}`} className="font-medium text-slate-800 hover:underline">
                    {h.asset_name}
                  </Link>
                </td>
                <td className="px-4 py-2.5 text-right">{Number(h.shares).toLocaleString()}</td>
                <td className="px-4 py-2.5 text-right">
                  <Money value={h.avg_cost} />
                </td>
                <td className="px-4 py-2.5 text-right font-medium text-slate-800">
                  <Money value={h.market_value} />
                </td>
                <td className={`px-4 py-2.5 text-right font-medium ${pnlColor(h.unrealized_pnl)}`}>
                  <Money value={h.unrealized_pnl} />
                  {h.unrealized_pnl_pct !== null && (
                    <span className="ml-1 text-xs">({(Number(h.unrealized_pnl_pct)).toFixed(1)}%)</span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-right">
                  <button
                    onClick={() => setSellingAssetId(sellingAssetId === h.asset_id ? null : h.asset_id)}
                    className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
                  >
                    Sell
                  </button>
                </td>
              </tr>
              {sellingAssetId === h.asset_id && (
                <tr>
                  <td colSpan={6} className="bg-slate-50 px-4 py-3">
                    <TradeForm assetId={h.asset_id} side="SELL" maxShares={Number(h.shares)} />
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  )
}
