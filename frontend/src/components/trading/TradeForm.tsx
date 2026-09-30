import { useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import * as tradeApi from '../../api/trade'
import { ErrorBanner } from '../common/ErrorBanner'

interface TradeFormProps {
  assetId: string
  side: 'BUY' | 'SELL'
  maxShares?: number
}

export function TradeForm({ assetId, side, maxShares }: TradeFormProps) {
  const [shares, setShares] = useState('')
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (sharesValue: number) =>
      side === 'BUY' ? tradeApi.buy({ asset_id: assetId, shares: sharesValue }) : tradeApi.sell({ asset_id: assetId, shares: sharesValue }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
      setShares('')
    },
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const value = Number(shares)
    if (value > 0) mutation.mutate(value)
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2">
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-500">Shares</label>
        <input
          type="number"
          min="0"
          step="any"
          max={maxShares}
          required
          value={shares}
          onChange={(e) => setShares(e.target.value)}
          className="w-28 rounded-md border border-slate-300 px-2.5 py-1.5 text-sm focus:border-slate-500 focus:outline-none"
        />
      </div>
      <button
        type="submit"
        disabled={mutation.isPending}
        className={`rounded-md px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 ${
          side === 'BUY' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-slate-700 hover:bg-slate-800'
        }`}
      >
        {mutation.isPending ? 'Submitting…' : side === 'BUY' ? 'Buy' : 'Sell'}
      </button>
      {mutation.isSuccess && <span className="text-sm text-emerald-600">Done.</span>}
      {mutation.isError && <ErrorBanner error={mutation.error} />}
    </form>
  )
}
