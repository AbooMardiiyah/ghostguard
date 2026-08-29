// VerdictBadge — consistent verdict colors across all sections.
// BLOCKED/BLOCK=red, FLAGGED/FLAG=amber, SEALED/CLEAR=emerald, ESCALATED=violet, INFO=zinc

import { Badge } from '@/components/ui/badge'

const STYLES: Record<string, string> = {
  BLOCK: 'bg-red-600/15 text-red-400 border-red-600/40',
  BLOCKED: 'bg-red-600/15 text-red-400 border-red-600/40',
  FLAG: 'bg-amber-500/15 text-amber-400 border-amber-500/40',
  FLAGGED: 'bg-amber-500/15 text-amber-400 border-amber-500/40',
  CLEAR: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40',
  SEALED: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40',
  APPROVED: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40',
  ESCALATED: 'bg-violet-500/15 text-violet-400 border-violet-500/40',
  INFO: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/40',
}

const LABELS: Record<string, string> = {
  BLOCK: 'BLOCK',
  FLAG: 'FLAG',
  CLEAR: 'CLEAR',
}

interface Props {
  verdict: string | null | undefined
  className?: string
}

export default function VerdictBadge({ verdict, className = '' }: Props) {
  const v = (verdict ?? 'INFO').toUpperCase()
  const style = STYLES[v] ?? STYLES.INFO
  const label = LABELS[v] ?? v
  return (
    <Badge variant="outline" className={`font-semibold tracking-wide ${style} ${className}`}>
      {label}
    </Badge>
  )
}
