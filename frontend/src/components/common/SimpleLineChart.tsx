import { useState } from 'react'

export interface LineChartPoint {
  x: string
  y: number
}

interface SimpleLineChartProps {
  points: LineChartPoint[]
  color?: string
  formatValue?: (v: number) => string
  formatDate?: (x: string) => string
  height?: number
}

const WIDTH = 640
const PAD_LEFT = 56
const PAD_RIGHT = 16
const PAD_TOP = 16
const PAD_BOTTOM = 28

// Single-series time-series line: 2px stroke, rounded caps, ~10% area wash,
// hairline recessive gridlines, crosshair+tooltip on hover. Colors/spec from
// the dataviz skill's reference palette (series-1 blue, validated against a
// white card surface) — no legend needed for a single series.
export function SimpleLineChart({
  points,
  color = '#2a78d6',
  formatValue = (v) => v.toLocaleString(),
  formatDate = (x) => x,
  height = 220,
}: SimpleLineChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null)

  if (points.length === 0) {
    return <div className="flex h-[220px] items-center justify-center text-sm text-slate-400">No data yet.</div>
  }

  const plotWidth = WIDTH - PAD_LEFT - PAD_RIGHT
  const plotHeight = height - PAD_TOP - PAD_BOTTOM
  const values = points.map((p) => p.y)
  const minY = Math.min(...values)
  const maxY = Math.max(...values)
  const range = maxY - minY || 1
  const yPad = range * 0.1

  const xFor = (i: number) => PAD_LEFT + (points.length === 1 ? plotWidth / 2 : (i / (points.length - 1)) * plotWidth)
  const yFor = (v: number) => PAD_TOP + plotHeight - ((v - minY + yPad) / (range + yPad * 2)) * plotHeight

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${xFor(i)} ${yFor(p.y)}`).join(' ')
  const areaPath = `${linePath} L ${xFor(points.length - 1)} ${PAD_TOP + plotHeight} L ${xFor(0)} ${PAD_TOP + plotHeight} Z`

  const gridSteps = 4
  const gridValues = Array.from({ length: gridSteps + 1 }, (_, i) => minY - yPad + ((range + yPad * 2) * i) / gridSteps)

  function handleMove(e: React.PointerEvent<SVGRectElement>) {
    const rect = e.currentTarget.getBoundingClientRect()
    const relX = ((e.clientX - rect.left) / rect.width) * WIDTH
    const nearest = Math.round(((relX - PAD_LEFT) / plotWidth) * (points.length - 1))
    setHoverIndex(Math.min(points.length - 1, Math.max(0, nearest)))
  }

  const hovered = hoverIndex !== null ? points[hoverIndex] : null

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${WIDTH} ${height}`} className="h-auto w-full" role="img" aria-label="Line chart">
        {gridValues.map((v, i) => (
          <g key={i}>
            <line
              x1={PAD_LEFT}
              x2={WIDTH - PAD_RIGHT}
              y1={yFor(v)}
              y2={yFor(v)}
              stroke="#e1e0d9"
              strokeWidth={1}
            />
            <text x={PAD_LEFT - 8} y={yFor(v)} textAnchor="end" dominantBaseline="middle" fontSize={11} fill="#898781">
              {formatValue(v)}
            </text>
          </g>
        ))}

        <path d={areaPath} fill={color} fillOpacity={0.1} stroke="none" />
        <path d={linePath} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />

        <circle cx={xFor(points.length - 1)} cy={yFor(points[points.length - 1].y)} r={4} fill={color} stroke="#fff" strokeWidth={2} />

        <text x={PAD_LEFT} y={height - 8} fontSize={11} fill="#898781">
          {formatDate(points[0].x)}
        </text>
        <text x={WIDTH - PAD_RIGHT} y={height - 8} textAnchor="end" fontSize={11} fill="#898781">
          {formatDate(points[points.length - 1].x)}
        </text>

        {hovered && (
          <line
            x1={xFor(hoverIndex!)}
            x2={xFor(hoverIndex!)}
            y1={PAD_TOP}
            y2={PAD_TOP + plotHeight}
            stroke="#c3c2b7"
            strokeWidth={1}
          />
        )}

        <rect
          x={PAD_LEFT}
          y={PAD_TOP}
          width={plotWidth}
          height={plotHeight}
          fill="transparent"
          onPointerMove={handleMove}
          onPointerLeave={() => setHoverIndex(null)}
        />
      </svg>
      {hovered && hoverIndex !== null && (
        <div
          className="pointer-events-none absolute top-2 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs shadow-sm"
          style={{ left: `${(xFor(hoverIndex) / WIDTH) * 100}%`, transform: 'translateX(-50%)' }}
        >
          <div className="font-semibold text-slate-900">{formatValue(hovered.y)}</div>
          <div className="text-slate-500">{formatDate(hovered.x)}</div>
        </div>
      )}
    </div>
  )
}
