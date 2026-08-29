// AnomalyTable — sortable table with expandable detail rows for anomaly queue.

import { useMemo, useState } from 'react'
import { ChevronDown, ChevronUp, FileText, ArrowUpDown, Download, FileSpreadsheet, Mail, FileDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import VerdictBadge from './VerdictBadge'
import ConfidenceBar from './ConfidenceBar'
import { fmtNaira, layerLabel } from '@/lib/format'
import { api } from '@/lib/api'
import type { Anomaly } from '@/lib/types'

interface Props {
  anomalies: Anomaly[]
  onDecide: (
    anomalyId: string,
    decision: 'block' | 'explain' | 'request_info',
    note: string,
  ) => Promise<void>
}

type SortKey = 'total_score' | 'employee_name' | 'verdict' | 'monthly_exposure'
type SortDir = 'asc' | 'desc'

const VERDICT_ORDER: Record<string, number> = { BLOCK: 3, FLAG: 2, CLEAR: 1 }

const PAGE_SIZE = 10

function SortHeader({ label, field, className = '', sortKey, onToggle }: {
  label: string; field: SortKey; className?: string; sortKey: SortKey; onToggle: (k: SortKey) => void
}) {
  return (
    <button
      onClick={() => onToggle(field)}
      className={`flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wider text-zinc-500 hover:text-zinc-300 ${className}`}
    >
      {label}
      <ArrowUpDown className={`h-3 w-3 ${sortKey === field ? 'text-emerald-400' : ''}`} />
    </button>
  )
}

function exportCsv(anomalies: Anomaly[]) {
  const header = 'Employee,Employee ID,Risk Score,Verdict,Exposure,Findings,Status\n'
  const rows = anomalies.map(a =>
    [
      `"${a.employee_name}"`,
      a.employee_id,
      `${a.total_score}%`,
      a.verdict,
      a.monthly_exposure,
      `"${a.findings.map(f => f.description).join('; ')}"`,
      a.status,
    ].join(',')
  ).join('\n')
  const blob = new Blob([header + rows], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `ghostguard-anomalies-${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

function exportExcel(anomalies: Anomaly[]) {
  const header = 'Employee,Employee ID,Risk Score,Verdict,Exposure,Findings,Status\n'
  const rows = anomalies.map(a =>
    [
      `"${a.employee_name}"`,
      a.employee_id,
      `${a.total_score}%`,
      a.verdict,
      a.monthly_exposure,
      `"${a.findings.map(f => f.description).join('; ')}"`,
      a.status,
    ].join(',')
  ).join('\n')
  const blob = new Blob([header + rows], { type: 'application/vnd.ms-excel' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `ghostguard-anomalies-${new Date().toISOString().slice(0, 10)}.xls`
  link.click()
  URL.revokeObjectURL(url)
}

export default function AnomalyTable({ anomalies, onDecide }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('total_score')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'open' | 'BLOCK' | 'FLAG'>('all')
  const [page, setPage] = useState(0)
  const [emailOpen, setEmailOpen] = useState(false)
  const [recipientEmail, setRecipientEmail] = useState('')
  const [sending, setSending] = useState(false)
  const [emailMsg, setEmailMsg] = useState<string | null>(null)

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const filtered = useMemo(() => {
    let list = [...anomalies]
    if (filter === 'open') list = list.filter((a) => a.status === 'open')
    else if (filter === 'BLOCK') list = list.filter((a) => a.verdict === 'BLOCK')
    else if (filter === 'FLAG') list = list.filter((a) => a.verdict === 'FLAG')
    return list
  }, [anomalies, filter])

  const sorted = useMemo(() => {
    const list = [...filtered]
    list.sort((a, b) => {
      let cmp = 0
      if (sortKey === 'total_score') cmp = a.total_score - b.total_score
      else if (sortKey === 'employee_name') cmp = a.employee_name.localeCompare(b.employee_name)
      else if (sortKey === 'verdict') cmp = (VERDICT_ORDER[a.verdict] ?? 0) - (VERDICT_ORDER[b.verdict] ?? 0)
      else if (sortKey === 'monthly_exposure') cmp = a.monthly_exposure - b.monthly_exposure
      return sortDir === 'desc' ? -cmp : cmp
    })
    return list
  }, [filtered, sortKey, sortDir])

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE)
  const paged = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div className="space-y-3">
      {/* Filter tabs + export */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {(['all', 'open', 'BLOCK', 'FLAG'] as const).map((f) => (
            <button
              key={f}
              onClick={() => { setFilter(f); setPage(0) }}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                filter === f
                  ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-600/40'
                  : 'text-zinc-500 hover:text-zinc-300 border border-zinc-800 hover:border-zinc-700'
              }`}
            >
              {f === 'all' ? `All (${anomalies.length})` :
               f === 'open' ? `Open (${anomalies.filter(a => a.status === 'open').length})` :
               f === 'BLOCK' ? `Block (${anomalies.filter(a => a.verdict === 'BLOCK').length})` :
               `Flag (${anomalies.filter(a => a.verdict === 'FLAG').length})`}
            </button>
          ))}
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button size="sm" variant="outline" className="border-zinc-700 text-zinc-400 hover:text-zinc-200">
              <Download className="mr-1.5 h-3.5 w-3.5" /> Export
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-800">
            <DropdownMenuItem onClick={() => exportCsv(sorted)} className="text-zinc-300 focus:bg-zinc-800 focus:text-zinc-100">
              <FileDown className="mr-2 h-4 w-4" /> Export as CSV
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => exportExcel(sorted)} className="text-zinc-300 focus:bg-zinc-800 focus:text-zinc-100">
              <FileSpreadsheet className="mr-2 h-4 w-4" /> Export as Excel
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => { setEmailOpen(true); setEmailMsg(null) }} className="text-zinc-300 focus:bg-zinc-800 focus:text-zinc-100">
              <Mail className="mr-2 h-4 w-4" /> Send via Email
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden">
        {/* Header row */}
        <div className="grid grid-cols-[1fr_90px_90px_130px_80px] gap-4 border-b border-zinc-800 bg-zinc-900 px-4 py-3">
          <SortHeader label="Employee" field="employee_name" sortKey={sortKey} onToggle={toggleSort} />
          <SortHeader label="Risk" field="total_score" sortKey={sortKey} onToggle={toggleSort} />
          <SortHeader label="Verdict" field="verdict" sortKey={sortKey} onToggle={toggleSort} />
          <SortHeader label="Exposure" field="monthly_exposure" className="hidden sm:flex" sortKey={sortKey} onToggle={toggleSort} />
          <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Status</span>
        </div>

        {/* Rows */}
        {paged.length === 0 && (
          <div className="px-5 py-8 text-center text-zinc-500">
            No anomalies match the current filter.
          </div>
        )}
        {paged.map((a) => (
          <AnomalyRow
            key={a.anomaly_id}
            anomaly={a}
            expanded={expandedId === a.anomaly_id}
            onToggle={() => setExpandedId(expandedId === a.anomaly_id ? null : a.anomaly_id)}
            onDecide={onDecide}
          />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-zinc-500">
            Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, sorted.length)} of {sorted.length}
          </span>
          <div className="flex gap-1">
            <Button
              size="sm" variant="outline"
              disabled={page === 0}
              onClick={() => setPage(p => p - 1)}
              className="h-7 border-zinc-700 text-zinc-400"
            >Prev</Button>
            <Button
              size="sm" variant="outline"
              disabled={page >= totalPages - 1}
              onClick={() => setPage(p => p + 1)}
              className="h-7 border-zinc-700 text-zinc-400"
            >Next</Button>
          </div>
        </div>
      )}

      {/* Email dialog */}
      {emailOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-900 p-6 shadow-xl">
            <h3 className="text-sm font-semibold text-zinc-100 mb-4">Send Anomaly Report via Email</h3>
            <input
              type="email"
              value={recipientEmail}
              onChange={(e) => setRecipientEmail(e.target.value)}
              placeholder="recipient@example.com"
              className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 placeholder:text-zinc-600 focus:border-emerald-500 focus:outline-none"
            />
            {emailMsg && (
              <p className={`mt-2 text-sm ${emailMsg.startsWith('Sent') ? 'text-emerald-400' : 'text-red-400'}`}>
                {emailMsg}
              </p>
            )}
            <div className="mt-4 flex justify-end gap-2">
              <Button size="sm" variant="outline" onClick={() => setEmailOpen(false)}
                className="border-zinc-700 text-zinc-300 hover:bg-zinc-800">Cancel</Button>
              <Button
                size="sm"
                disabled={sending || !recipientEmail}
                onClick={async () => {
                  setSending(true)
                  setEmailMsg(null)
                  try {
                    const res = await api.sendAnomalyEmail(recipientEmail, sorted)
                    setEmailMsg(res.sent ? 'Sent successfully!' : 'SMTP not configured — check backend .env')
                  } catch (e) {
                    setEmailMsg(e instanceof Error ? e.message : 'Failed to send')
                  } finally {
                    setSending(false)
                  }
                }}
                className="bg-emerald-600 hover:bg-emerald-500"
              >
                {sending ? 'Sending...' : 'Send Report'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


// --- Individual row ---

function AnomalyRow({
  anomaly,
  expanded,
  onToggle,
  onDecide,
}: {
  anomaly: Anomaly
  expanded: boolean
  onToggle: () => void
  onDecide: Props['onDecide']
}) {
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState('')
  const [pending, setPending] = useState<'block' | 'explain' | 'request_info' | null>(null)
  const decided = anomaly.status !== 'open'

  const confirm = async () => {
    if (!pending) return
    setBusy(true)
    try {
      await onDecide(anomaly.anomaly_id, pending, note)
      setPending(null)
      setNote('')
    } finally {
      setBusy(false)
    }
  }

  const statusLabel: Record<string, { text: string; cls: string }> = {
    explained: { text: 'Explained', cls: 'text-emerald-400' },
    blocked: { text: 'Blocked', cls: 'text-red-400' },
    escalated: { text: 'Escalated', cls: 'text-violet-400' },
    open: { text: 'Open', cls: 'text-amber-400' },
  }
  const st = statusLabel[anomaly.status] ?? { text: anomaly.status, cls: 'text-zinc-400' }

  return (
    <div className="border-b border-zinc-800/60 last:border-0">
      {/* Summary row */}
      <button
        onClick={onToggle}
        className="grid w-full grid-cols-[1fr_90px_90px_130px_80px] gap-4 px-4 py-3 text-left hover:bg-zinc-800/30 transition-colors items-center"
      >
        <div className="min-w-0">
          <span className="text-sm font-semibold text-zinc-100 truncate block">{anomaly.employee_name}</span>
          <span className="text-[11px] text-zinc-500">{anomaly.employee_id} · {anomaly.findings.length} finding{anomaly.findings.length !== 1 ? 's' : ''}</span>
        </div>
        <ConfidenceBar score={anomaly.total_score} />
        <VerdictBadge verdict={anomaly.verdict} />
        <span className="text-sm tabular-nums text-zinc-300 hidden sm:block">{fmtNaira(anomaly.monthly_exposure)}</span>
        <div className="flex items-center justify-between">
          <span className={`text-xs font-medium ${st.cls}`}>{st.text}</span>
          {expanded ? <ChevronUp className="h-3.5 w-3.5 text-zinc-500" /> : <ChevronDown className="h-3.5 w-3.5 text-zinc-500" />}
        </div>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-zinc-800/40 bg-zinc-950/40 px-4 py-4 space-y-4">
          {/* Exposure on mobile */}
          <div className="sm:hidden text-sm text-zinc-300">Exposure: {fmtNaira(anomaly.monthly_exposure)}/mo</div>

          {/* AI explanation */}
          {anomaly.explanation &&
            !anomaly.explanation.includes('Analysis completed. See detailed findings') && (
              <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-emerald-500/60 mb-1">AI Analysis</div>
                <p className="text-sm text-zinc-300">{anomaly.explanation}</p>
              </div>
            )}

          {/* Findings */}
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-600 mb-2">Layer Findings</div>
            <div className="space-y-1.5">
              {anomaly.findings.map((f, i) => (
                <div key={i} className="flex items-start justify-between gap-3 rounded-lg border border-zinc-800/40 bg-zinc-900/40 px-3 py-2">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="shrink-0 rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] font-semibold text-zinc-400">
                        {layerLabel(f.layer)}
                      </span>
                      <span className="text-sm text-zinc-300">{f.description}</span>
                    </div>
                    {Object.keys(f.evidence ?? {}).length > 0 && (
                      <div className="mt-1 flex items-start gap-1.5 text-[11px] text-zinc-600">
                        <FileText className="mt-0.5 h-3 w-3 shrink-0" />
                        <code className="break-all">
                          {Object.entries(f.evidence)
                            .map(([k, v]) => `${k}=${String(v)}`)
                            .join(' · ')}
                        </code>
                      </div>
                    )}
                  </div>
                  <span className={`shrink-0 text-xs font-bold tabular-nums ${
                    f.points >= 40 ? 'text-red-400' : f.points >= 25 ? 'text-amber-400' : 'text-zinc-500'
                  }`}>
                    +{f.points}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-2 border-t border-zinc-800/40">
            {decided ? (
              <span className={`text-sm font-medium ${st.cls}`}>
                {st.text}{anomaly.decided_by ? ` · by ${anomaly.decided_by}` : ''}
              </span>
            ) : pending ? (
              <div className="w-full space-y-2">
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Add a note..."
                  className="min-h-[3rem] w-full rounded-lg border border-zinc-800 bg-zinc-950 p-2.5 text-sm text-zinc-300 placeholder:text-zinc-700 focus:border-emerald-500 focus:outline-none"
                />
                <div className="flex gap-2">
                  <Button
                    size="sm" disabled={busy} onClick={confirm}
                    className={pending === 'block' ? 'bg-red-600/80 hover:bg-red-600' : 'border-zinc-700 bg-transparent text-zinc-300 hover:bg-zinc-800'}
                  >
                    Confirm {pending === 'block' ? 'Block' : pending === 'explain' ? 'Explained' : 'Info Request'}
                  </Button>
                  <Button size="sm" variant="ghost" disabled={busy} onClick={() => { setPending(null); setNote('') }}
                    className="text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
                  >Cancel</Button>
                </div>
              </div>
            ) : (
              <div className="flex gap-2">
                <Button size="sm" variant="destructive" onClick={() => setPending('block')}
                  className="bg-red-600/80 hover:bg-red-600">Block Payment</Button>
                <Button size="sm" variant="outline" onClick={() => setPending('explain')}
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800">Mark Explained</Button>
                <Button size="sm" variant="outline" onClick={() => setPending('request_info')}
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800">Request Info</Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
