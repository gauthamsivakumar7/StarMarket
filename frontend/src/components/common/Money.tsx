interface MoneyProps {
  value: string | number
  className?: string
}

export function Money({ value, className }: MoneyProps) {
  const num = typeof value === 'string' ? Number(value) : value
  const formatted = Number.isFinite(num)
    ? num.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    : '—'
  return <span className={className}>{formatted}</span>
}
