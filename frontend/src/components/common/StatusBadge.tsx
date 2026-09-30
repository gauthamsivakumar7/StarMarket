const COLOR_MAP: Record<string, string> = {
  draft: 'bg-slate-100 text-slate-700',
  invalid: 'bg-red-100 text-red-700',
  resolved: 'bg-sky-100 text-sky-700',
  backtested: 'bg-indigo-100 text-indigo-700',
  active: 'bg-emerald-100 text-emerald-700',
  paused: 'bg-amber-100 text-amber-700',
  archived: 'bg-slate-100 text-slate-500',
  pending_approval: 'bg-amber-100 text-amber-700',
  approved: 'bg-sky-100 text-sky-700',
  rejected: 'bg-red-100 text-red-700',
  expired: 'bg-slate-100 text-slate-500',
  executed: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-red-100 text-red-700',
  partially_filled: 'bg-amber-100 text-amber-700',
  pending: 'bg-slate-100 text-slate-700',
  running: 'bg-sky-100 text-sky-700',
  completed: 'bg-emerald-100 text-emerald-700',
}

export function StatusBadge({ status }: { status: string }) {
  const classes = COLOR_MAP[status] ?? 'bg-slate-100 text-slate-700'
  return (
    <span className={`inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ${classes}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}
