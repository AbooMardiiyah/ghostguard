// AnomalyCard — expandable anomaly card with reason-code surfacing,
// confidence bar, evidence citations, and human-gate action buttons.

import { useState } from 'react'
import { ChevronDown, ChevronUp, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import VerdictBadge from './VerdictBadge'
import ConfidenceBar from './ConfidenceBar'
import { fmtNaira, layerLabel } from '@/lib/format'
import type { Anomaly } from '@/lib/types'

interface Props {
  anomaly: Anomaly
  onDecide: (
    anomalyId: string,
    decision: 'block' | 'explain' | 'request_info',
    note: string,
  ) => Promise<void>
}

const STATUS_LABEL: Record<string, { text: string; cls: string }> = {
  explained: { text: 'Explained', cls: 'text-emerald-400' },
  blocked: { text: 'Payment blocked', cls: 'text-red-400' },
  escalated: { text: 'Escalated — info requested', cls: 'text-violet-400' },
}

export default function AnomalyCard({ anomaly, onDecide }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState('')
  const [pending, setPending] = useState<'block' | 'explain' | 'request_info' | null>(null)
  const decided = anomaly.status !== 'open'
  const statusInfo = STATUS_LABEL[anomaly.status]

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

  const cancel = () => {
    setPending(null)
    setNote('')
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <VerdictBadge verdict={anomaly.verdict} />
            <span className="text-xs font-mono text-zinc-600">{anomaly.anomaly_id}</span>
          </div>
          <h3 className="mt-2 text-base font-semibold text-zinc-100">{anomaly.employee_name}</h3>
          <p className="text-sm text-zinc-500">
            {anomaly.employee_id} · {fmtNaira(anomaly.monthly_exposure)}/month exposure
          </p>
        </div>
        <ConfidenceBar score={anomaly.total_score} />
      </div>

      {/* WHY FLAGGED — visible without expanding */}
      <div className="mt-4">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
          Why flagged
        </div>
        <ul className="mt-1.5 space-y-1">
          {anomaly.findings.slice(0, expanded ? undefined : 3).map((f, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-zinc-300">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500/70" />
              <span>
                <span className="text-zinc-500">{layerLabel(f.layer)}:</span> {f.description}
                <span className="ml-1 text-xs text-zinc-600">+{f.points}pts</span>
              </span>
            </li>
          ))}
        </ul>
        {!expanded && anomaly.findings.length > 3 && (
          <div className="mt-1 text-xs text-zinc-600">
            +{anomaly.findings.length - 3} more findings…
          </div>
        )}
      </div>

      {/* Explanation — skip generic mock fallback, show only useful LLM text */}
      {anomaly.explanation &&
        !anomaly.explanation.includes("Analysis completed. See detailed findings") && (
          <p className="mt-3 rounded-lg border border-zinc-800/80 bg-zinc-950/60 p-3 text-sm italic text-zinc-400">
            {anomaly.explanation}
          </p>
        )}

      {/* Actions / status */}
      <div className="mt-4 flex items-center justify-between">
        {decided ? (
          <span className={`text-sm font-medium ${statusInfo?.cls ?? 'text-zinc-400'}`}>
            {statusInfo?.text ?? anomaly.status}
            {anomaly.decided_by ? ` · by ${anomaly.decided_by}` : ''}
          </span>
        ) : pending ? (
          <div className="w-full space-y-2">
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Add a note (e.g. Yusuf & Fatima Bello are siblings — shared address is expected)"
              className="min-h-[4rem] w-full rounded-lg border border-zinc-800 bg-zinc-950 p-2.5 text-sm text-zinc-300 placeholder:text-zinc-700 focus:border-emerald-500 focus:outline-none"
            />
            <div className="flex gap-2">
              <Button
                size="sm"
                disabled={busy}
                onClick={confirm}
                className={
                  pending === 'block'
                    ? 'bg-red-600/80 hover:bg-red-600'
                    : 'border-zinc-700 bg-transparent text-zinc-300 hover:bg-zinc-800'
                }
              >
                Confirm {pending === 'block' ? 'Block' : pending === 'explain' ? 'Explained' : 'Info Request'}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                disabled={busy}
                onClick={cancel}
                className="text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="destructive"
              onClick={() => setPending('block')}
              className="bg-red-600/80 hover:bg-red-600"
            >
              Block Payment
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setPending('explain')}
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            >
              Mark Explained
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setPending('request_info')}
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            >
              Request Info
            </Button>
          </div>
        )}
        {pending ? null : (
          <button
            onClick={() => setExpanded((e) => !e)}
            className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300"
          >
            {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            {expanded ? 'Hide evidence' : 'Full evidence + citations'}
          </button>
        )}
      </div>

      {/* Expanded evidence */}
      {expanded && (
        <div className="mt-4 space-y-2 border-t border-zinc-800 pt-4">
          {anomaly.findings.map((f, i) => (
            <div key={i} className="rounded-lg border border-zinc-800/60 bg-zinc-950/40 p-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-zinc-300">
                  {layerLabel(f.layer)} · {f.signal}
                </span>
                <span className="text-xs text-zinc-600">source: {f.source}</span>
              </div>
              <p className="mt-1 text-sm text-zinc-400">{f.description}</p>
              {Object.keys(f.evidence ?? {}).length > 0 && (
                <div className="mt-2 flex items-start gap-1.5 text-xs text-zinc-600">
                  <FileText className="mt-0.5 h-3 w-3 shrink-0" />
                  <code className="break-all">
                    {Object.entries(f.evidence)
                      .map(([k, v]) => `${k}=${String(v)}`)
                      .join(' · ')}
                  </code>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
