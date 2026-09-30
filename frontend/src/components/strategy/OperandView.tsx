import type { Operand } from '../../types/strategySpec'

export function OperandView({ op }: { op: Operand }) {
  if (op.type === 'constant') {
    return <span>{op.value}</span>
  }
  const params = Object.entries(op.params)
    .map(([k, v]) => `${k}=${v}`)
    .join(', ')
  return (
    <span>
      {op.name}
      {params && `(${params})`} of <span className="font-semibold">{op.symbol}</span>
    </span>
  )
}
