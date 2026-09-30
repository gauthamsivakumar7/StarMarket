import { useState, type FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { createStrategy } from '../api/strategies'
import { ApiError } from '../api/client'
import { ErrorBanner } from '../components/common/ErrorBanner'

const EXAMPLE =
  'Universe: SPY. Entry: SMA(close,20) crosses_above SMA(close,50) AND VIX < 20. ' +
  'Risk: max_portfolio_risk=1%, stop_loss=2%. Execution: MARKET.'

export function StrategyCreatePage() {
  const navigate = useNavigate()
  const [thesisText, setThesisText] = useState('')
  const [name, setName] = useState('')

  const mutation = useMutation({
    mutationFn: () => createStrategy(thesisText, name || undefined),
    onSuccess: (strategy) => navigate(`/strategies/${strategy.id}`),
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    mutation.mutate()
  }

  const issues = mutation.error instanceof ApiError ? mutation.error.issues : []

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">New strategy</h1>
        <p className="text-sm text-slate-500">
          Describe a trading thesis in plain language. It'll be translated into a structured strategy, then you can
          resolve, backtest, and — only after your explicit approval — trade it.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Name (optional)</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. SPY SMA crossover"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Trading thesis</label>
          <textarea
            required
            rows={6}
            value={thesisText}
            onChange={(e) => setThesisText(e.target.value)}
            placeholder={EXAMPLE}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={() => setThesisText(EXAMPLE)}
            className="mt-1 text-xs font-medium text-slate-500 hover:underline"
          >
            Use example thesis
          </button>
        </div>

        {mutation.error && <ErrorBanner error={mutation.error} />}
        {issues.length > 0 && (
          <ul className="space-y-1">
            {issues.map((issue, i) => (
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
        )}

        <button
          type="submit"
          disabled={mutation.isPending}
          className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {mutation.isPending ? 'Translating thesis…' : 'Create strategy'}
        </button>
      </form>
    </div>
  )
}
