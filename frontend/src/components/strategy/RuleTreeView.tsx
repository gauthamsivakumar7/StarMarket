import type { BooleanOp, Condition, RuleNode } from '../../types/strategySpec'
import { OperandView } from './OperandView'

const OP_LABEL: Record<string, string> = {
  crosses_above: 'crosses above',
  crosses_below: 'crosses below',
  '>': '>',
  '<': '<',
  '>=': '>=',
  '<=': '<=',
  '==': '=',
}

function ConditionView({ node }: { node: Condition }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-sm text-slate-700">
      <OperandView op={node.left} /> <span className="font-semibold text-slate-900">{OP_LABEL[node.op]}</span>{' '}
      <OperandView op={node.right} />
    </div>
  )
}

function BooleanGroupView({ node }: { node: BooleanOp }) {
  return (
    <div className="space-y-2 border-l-2 border-slate-300 pl-3">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">{node.type}</span>
      {node.children.map((child, i) => (
        <div key={i}>
          {i > 0 && node.type !== 'not' && (
            <div className="mb-2 text-xs font-medium uppercase text-slate-400">{node.type}</div>
          )}
          <RuleTreeView node={child} />
        </div>
      ))}
    </div>
  )
}

export function RuleTreeView({ node }: { node: RuleNode }) {
  return node.type === 'condition' ? <ConditionView node={node} /> : <BooleanGroupView node={node} />
}
