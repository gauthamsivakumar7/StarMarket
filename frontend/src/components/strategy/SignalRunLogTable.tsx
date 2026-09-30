import { Link } from 'react-router-dom'
import type { SignalRun } from '../../types/signalRun'

export function SignalRunLogTable({ runs }: { runs: SignalRun[] }) {
  if (runs.length === 0) {
    return <p className="text-sm text-slate-500">No evaluations yet. Click "Evaluate now" to check the live signal.</p>
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="border-b border-slate-100 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-400">
          <tr>
            <th className="px-4 py-2 font-medium">When</th>
            <th className="px-4 py-2 font-medium">Triggered by</th>
            <th className="px-4 py-2 font-medium">Signal</th>
            <th className="px-4 py-2 font-medium">Action</th>
            <th className="px-4 py-2 font-medium">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {runs.map((run) => (
            <tr key={run.id} className="hover:bg-slate-50">
              <td className="px-4 py-2.5 text-slate-500">
                {run.created_at ? new Date(run.created_at).toLocaleString() : '—'}
              </td>
              <td className="px-4 py-2.5 text-slate-500">{run.triggered_by.replace('_', ' ')}</td>
              <td className="px-4 py-2.5">
                <span className={run.triggered ? 'font-medium text-emerald-600' : 'text-slate-400'}>
                  {run.triggered ? 'Triggered' : 'No signal'}
                </span>
              </td>
              <td className="px-4 py-2.5 text-slate-600">
                {run.action === 'plan_generated' && run.execution_plan_id ? (
                  <Link to="#execution-plans" className="text-slate-800 hover:underline">
                    Plan #{run.execution_plan_id} generated
                  </Link>
                ) : (
                  run.action.replace(/_/g, ' ')
                )}
              </td>
              <td className="px-4 py-2.5 text-red-600">{run.error_message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
