// AuditTrail — chronological hash-chained event log + sealed packet download.

import { useCallback, useEffect, useMemo, useState } from 'react'
import { Download, RefreshCw, ShieldCheck, ShieldX, Search } from 'lucide-react'
import { api } from '@/lib/api'
import { fmtDateTime, shortHash } from '@/lib/format'
import type { AuditChainStatus, AuditEvent } from '@/lib/types'
import VerdictBadge from '@/components/VerdictBadge'
import { Button } from '@/components/ui/button'

const PAGE_SIZE = 15

const EVENT_TYPES = ['all', 'scan', 'decision', 'defense', 'identity', 'upload', 'system'] as const
type EventFilter = (typeof EVENT_TYPES)[number]

function classifyEvent(ev: AuditEvent): EventFilter {
  const a = ev.action.toLowerCase()
  const t = ev.event_type.toLowerCase()
  if (t.includes('scan') || a.includes('scan')) return 'scan'
  if (t.includes('decision') || a.includes('block') || a.includes('explain')) return 'decision'
  if (t.includes('defense') || a.includes('defense') || a.includes('red_team')) return 'defense'
  if (t.includes('identity') || a.includes('verif')) return 'identity'
  if (t.includes('upload') || a.includes('upload') || a.includes('csv')) return 'upload'
  return 'system'
}

export default function AuditTrail() {
  const [events, setEvents] = useState<AuditEvent[] | null>(null)
  const [chain, setChain] = useState<AuditChainStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<EventFilter>('all')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)

  const load = useCallback(async () => {
    try {
      const [trail, verify] = await Promise.all([api.auditTrail(), api.auditVerify()])
      setEvents(trail.events)
      setChain(verify)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Backend unreachable')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const filtered = useMemo(() => {
    if (!events) return []
    let list = events
    if (filter !== 'all') {
      list = list.filter((ev) => classifyEvent(ev) === filter)
    }
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(
        (ev) =>
          ev.action.toLowerCase().includes(q) ||
          ev.actor.toLowerCase().includes(q) ||
          (ev.target?.toLowerCase().includes(q) ?? false) ||
          (ev.detail?.toLowerCase().includes(q) ?? false),
      )
    }
    return list
  }, [events, filter, search])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paged = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  const handleFilterChange = (f: EventFilter) => {
    setFilter(f)
    setPage(0)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-zinc-100">Audit Trail</h1>
          <p className="text-sm text-zinc-500">
            Append-only, hash-chained event log.
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={load} size="sm" variant="outline" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800">
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Refresh
          </Button>
          <a href={api.auditPacketUrl()} download>
            <Button size="sm" className="bg-emerald-600 font-semibold hover:bg-emerald-500">
              <Download className="mr-1.5 h-3.5 w-3.5" /> Sealed Packet
            </Button>
          </a>
        </div>
      </div>

      {/* Chain status */}
      {chain && (
        <div
          className={`flex items-center justify-between rounded-xl border px-4 py-3 ${
            chain.chain_valid
              ? 'border-emerald-500/40 bg-emerald-500/10'
              : 'border-red-600/40 bg-red-600/10'
          }`}
        >
          <div className="flex items-center gap-3">
            {chain.chain_valid ? (
              <ShieldCheck className="h-5 w-5 text-emerald-400" />
            ) : (
              <ShieldX className="h-5 w-5 text-red-400" />
            )}
            <div>
              <p className={`text-sm font-semibold ${chain.chain_valid ? 'text-emerald-300' : 'text-red-300'}`}>
                {chain.chain_valid ? 'Hash chain intact' : 'CHAIN COMPROMISED'}
              </p>
              <p className="text-xs text-zinc-500">{chain.events_count} sealed events</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-zinc-600">Latest hash</div>
            <code className="text-xs text-zinc-400">{shortHash(chain.latest_hash, 16)}</code>
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-600/40 bg-red-600/10 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Filters + search */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {EVENT_TYPES.map((f) => (
            <button
              key={f}
              onClick={() => handleFilterChange(f)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                filter === f
                  ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-600/40'
                  : 'text-zinc-500 hover:text-zinc-300 border border-zinc-800 hover:border-zinc-700'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-600" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0) }}
            placeholder="Search events..."
            className="w-full rounded-lg border border-zinc-800 bg-zinc-950 py-1.5 pl-8 pr-3 text-sm text-zinc-300 placeholder:text-zinc-600 focus:border-emerald-500 focus:outline-none sm:w-56"
          />
        </div>
      </div>

      {/* Event table */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[1fr_100px_140px_100px] gap-2 border-b border-zinc-800 bg-zinc-900 px-4 py-2.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Event</span>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Verdict</span>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 hidden sm:block">Timestamp</span>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 text-right">Chain</span>
        </div>

        {!events && (
          <div className="px-5 py-10 text-center text-zinc-600">Loading…</div>
        )}
        {events && paged.length === 0 && (
          <div className="px-5 py-8 text-center text-zinc-500">
            {events.length === 0
              ? 'No events yet — run a scan or defense simulation to start the trail.'
              : 'No events match the current filter.'}
          </div>
        )}
        {paged.map((ev) => (
          <div
            key={ev.event_id}
            className="grid grid-cols-[1fr_100px_140px_100px] gap-2 items-center border-b border-zinc-800/60 last:border-0 px-4 py-2.5 hover:bg-zinc-800/20 transition-colors"
          >
            <div className="min-w-0">
              <span className="text-sm font-medium text-zinc-200 truncate block">{ev.action}</span>
              <span className="text-[11px] text-zinc-500">
                {ev.actor}{ev.target ? ` · ${ev.target}` : ''}
              </span>
            </div>
            <div>
              {ev.verdict ? <VerdictBadge verdict={ev.verdict} /> : <span className="text-xs text-zinc-600">—</span>}
            </div>
            <span className="text-xs tabular-nums text-zinc-400 hidden sm:block">{fmtDateTime(ev.timestamp)}</span>
            <code className="text-[11px] text-zinc-600 text-right truncate">{shortHash(ev.chain_hash)}</code>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-zinc-500">
            Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} of {filtered.length}
          </span>
          <div className="flex gap-1">
            <Button
              size="sm" variant="outline"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className="h-7 border-zinc-700 text-zinc-400"
            >Prev</Button>
            <Button
              size="sm" variant="outline"
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className="h-7 border-zinc-700 text-zinc-400"
            >Next</Button>
          </div>
        </div>
      )}
    </div>
  )
}
