import type { RiskAssessment } from '../../types/executionPlan'

export function RiskAssessmentCard({ assessment, title }: { assessment: RiskAssessment; title: string }) {
  return (
    <div className="rounded-md border border-slate-200 p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">{title}</span>
        <span className={`text-xs font-medium ${assessment.passed ? 'text-emerald-600' : 'text-red-600'}`}>
          {assessment.passed ? 'Passed' : 'Blocked'}
        </span>
      </div>
      {assessment.blocking_issues.length > 0 && (
        <ul className="mb-1.5 space-y-1">
          {assessment.blocking_issues.map((issue, i) => (
            <li key={i} className="rounded bg-red-50 px-2 py-1 text-xs text-red-700">
              {issue}
            </li>
          ))}
        </ul>
      )}
      {assessment.warnings.length > 0 && (
        <ul className="space-y-1">
          {assessment.warnings.map((warning, i) => (
            <li key={i} className="rounded bg-amber-50 px-2 py-1 text-xs text-amber-700">
              {warning}
            </li>
          ))}
        </ul>
      )}
      {assessment.blocking_issues.length === 0 && assessment.warnings.length === 0 && (
        <p className="text-xs text-slate-400">No issues.</p>
      )}
    </div>
  )
}
