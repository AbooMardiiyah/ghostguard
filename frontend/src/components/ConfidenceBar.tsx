// ConfidenceBar — percentage display with color-coded progress bar.

interface Props {
  score: number // 0-100
}

export default function ConfidenceBar({ score }: Props) {
  const pct = Math.min(100, Math.max(0, score))
  const color =
    pct >= 70 ? 'bg-red-500' : pct >= 30 ? 'bg-amber-500' : 'bg-emerald-500'
  const textColor =
    pct >= 70 ? 'text-red-400' : pct >= 30 ? 'text-amber-400' : 'text-emerald-400'

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-16 rounded-full bg-zinc-800 overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-xs font-bold tabular-nums ${textColor}`}>{pct}%</span>
    </div>
  )
}
