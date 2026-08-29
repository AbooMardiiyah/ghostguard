// KPICard — large number + label for the Command Center KPI row.

import type { LucideIcon } from 'lucide-react'

interface Props {
  label: string
  value: string | number
  sub?: string
  icon?: LucideIcon
  accent?: 'emerald' | 'amber' | 'red' | 'zinc'
}

const ACCENTS: Record<string, string> = {
  emerald: 'text-emerald-400',
  amber: 'text-amber-400',
  red: 'text-red-400',
  zinc: 'text-zinc-100',
}

export default function KPICard({ label, value, sub, icon: Icon, accent = 'zinc' }: Props) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">{label}</span>
        {Icon && <Icon className="h-4 w-4 text-zinc-600" />}
      </div>
      <div className={`mt-2 text-3xl font-bold tabular-nums ${ACCENTS[accent]}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-zinc-500">{sub}</div>}
    </div>
  )
}
