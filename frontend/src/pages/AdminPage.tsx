import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import * as adminApi from '../api/admin'
import { ErrorBanner } from '../components/common/ErrorBanner'

interface ActionButtonProps {
  label: string
  description: string
  action: () => Promise<unknown>
}

function ActionCard({ label, description, action }: ActionButtonProps) {
  const [result, setResult] = useState<string | null>(null)
  const mutation = useMutation({
    mutationFn: action,
    onSuccess: (data) => setResult(JSON.stringify(data, null, 2)),
  })

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h2 className="font-medium text-slate-900">{label}</h2>
      <p className="mb-3 text-sm text-slate-500">{description}</p>
      <button
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
      >
        {mutation.isPending ? 'Running…' : 'Run'}
      </button>
      <ErrorBanner error={mutation.error} />
      {result && (
        <pre className="mt-3 max-h-48 overflow-auto rounded-md bg-slate-50 p-3 text-xs text-slate-600">{result}</pre>
      )}
    </div>
  )
}

export function AdminPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">Admin</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <ActionCard
          label="Seed athletes"
          description="Insert the default athlete assets if the database is empty."
          action={adminApi.seedAssets}
        />
        <ActionCard
          label="Update prices (simulated)"
          description="Bump every asset's price with a small random walk."
          action={adminApi.updatePricesSimulated}
        />
        <ActionCard
          label="Sync market data (live)"
          description="Refresh equity asset prices from live market data (yfinance)."
          action={adminApi.syncMarketData}
        />
        <ActionCard
          label="Run monitoring sweep"
          description="Evaluate every active strategy's live signal and generate execution plans where warranted."
          action={adminApi.runMonitoringSweep}
        />
      </div>
    </div>
  )
}
