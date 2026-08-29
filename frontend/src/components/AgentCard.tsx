// AgentCard — differentiated per-agent status card.

import { Landmark, ScanSearch, ShieldCheck, Swords, type LucideIcon } from 'lucide-react'
import type { AgentStatus } from '@/lib/types'
import { fmtDateTime } from '@/lib/format'

const AGENT_ICONS: Record<string, LucideIcon> = {
  verifier: ScanSearch,
  auditor: Landmark,
  guardian: ShieldCheck,
  redteam: Swords,
}

const STATE_STYLE: Record<string, { dot: string; label: string }> = {
  active: { dot: 'bg-emerald-500', label: 'Active' },
  idle: { dot: 'bg-zinc-500', label: 'Idle' },
  armed: { dot: 'bg-amber-500', label: 'Armed' },
  error: { dot: 'bg-red-500 animate-pulse', label: 'Error' },
}

export default function AgentCard({ agent }: { agent: AgentStatus }) {
  const Icon = AGENT_ICONS[agent.agent_id] ?? ShieldCheck
  const state = STATE_STYLE[agent.state] ?? STATE_STYLE.idle
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-emerald-400" />
          <span className="text-sm font-semibold text-zinc-200">{agent.name}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`h-2 w-2 rounded-full ${state.dot}`} />
          <span className="text-xs text-zinc-500">{state.label}</span>
        </div>
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-xs text-zinc-500">
          {agent.summary_metric ?? `${agent.tasks_completed} tasks`}
        </span>
        {agent.tasks_failed > 0 && (
          <span className="text-xs text-red-400">{agent.tasks_failed} failed</span>
        )}
      </div>
      {agent.last_run && (
        <div className="mt-1 text-[11px] text-zinc-600">Last run {fmtDateTime(agent.last_run)}</div>
      )}
    </div>
  )
}
