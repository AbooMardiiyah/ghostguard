// Shell — app shell: 4-section sidebar + top bar.

import type { ReactNode } from 'react'
import { Clock, LayoutDashboard, Plug, ScrollText, Shield, Zap } from 'lucide-react'

export type SectionKey = 'command' | 'defense' | 'integrations' | 'scheduler' | 'audit'

const NAV: { key: SectionKey; label: string; icon: typeof LayoutDashboard }[] = [
  { key: 'command', label: 'Command Center', icon: LayoutDashboard },
  { key: 'defense', label: 'Live Defense', icon: Zap },
  { key: 'integrations', label: 'Integrations', icon: Plug },
  { key: 'scheduler', label: 'Scheduler', icon: Clock },
  { key: 'audit', label: 'Audit Trail', icon: ScrollText },
]

interface Props {
  active: SectionKey
  onNavigate: (s: SectionKey) => void
  onSignOut: () => void
  children: ReactNode
}

export default function Shell({ active, onNavigate, onSignOut, children }: Props) {
  return (
    <div className="flex min-h-screen bg-zinc-950 text-zinc-100">
      {/* Sidebar */}
      <aside className="flex w-60 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950">
        <div className="flex items-center gap-2.5 border-b border-zinc-800 px-5 py-5">
          <Shield className="h-6 w-6 text-emerald-400" />
          <div>
            <div className="text-sm font-bold tracking-wide">GhostGuard</div>
            <div className="text-[11px] text-zinc-500">Sterling Distributors Ltd</div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => onNavigate(key)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                active === key
                  ? 'bg-emerald-500/10 font-medium text-emerald-400'
                  : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>

        <div className="border-t border-zinc-800 px-5 py-4">
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-amber-400">
              Sandbox mode
            </div>
            <div className="text-[11px] text-zinc-500">Dojah test environment</div>
          </div>
          <div className="mt-3 flex items-center justify-between">
            <span className="text-xs text-zinc-400">👤 Hamzat Tiamiyu</span>
            <button onClick={onSignOut} className="text-xs text-zinc-600 hover:text-zinc-300">
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="min-w-0 flex-1">
        <div className="mx-auto max-w-6xl px-6 py-6">{children}</div>
      </main>
    </div>
  )
}
