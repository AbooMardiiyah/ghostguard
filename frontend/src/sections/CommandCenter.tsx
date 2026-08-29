// CommandCenter — the "value on arrival" screen.
// Risk banner, KPI cards, anomaly queue with human gate, agent fleet.

import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, BadgeCheck, Play, RefreshCw, ShieldAlert, Users } from 'lucide-react'
import { api } from '@/lib/api'
import { fmtNaira } from '@/lib/format'
import type { DashboardResponse } from '@/lib/types'
import KPICard from '@/components/KPICard'
import AgentCard from '@/components/AgentCard'
import AnomalyTable from '@/components/AnomalyTable'
import { Button } from '@/components/ui/button'

export default function CommandCenter() {
  const [data, setData] = useState<DashboardResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [scanning, setScanning] = useState(false)

  const load = useCallback(async () => {
    try {
      setData(await api.dashboard())
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Backend unreachable')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const runScan = async () => {
    setScanning(true)
    try {
      await api.scanPayroll()
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Scan failed')
    } finally {
      setScanning(false)
    }
  }

  const decide = async (
    anomalyId: string,
    decision: 'block' | 'explain' | 'request_info',
    note: string,
  ) => {
    await api.decide({ anomaly_id: anomalyId, decision, actor: 'A. Danjuma', note })
    await load()
  }

  if (error && !data) {
    return (
      <div className="rounded-xl border border-red-600/40 bg-red-600/10 p-6 text-red-300">
        <p className="font-semibold">Cannot reach the GhostGuard backend</p>
        <p className="mt-1 text-sm text-red-400/80">{error}</p>
        <p className="mt-2 text-xs text-zinc-500">
          Start it with: <code>uvicorn app.main:app --port 8000</code>
        </p>
        <Button onClick={load} variant="outline" className="mt-4 border-zinc-700">
          <RefreshCw className="mr-2 h-4 w-4" /> Retry
        </Button>
      </div>
    )
  }

  if (!data) {
    return <div className="py-20 text-center text-zinc-600">Loading dashboard…</div>
  }

  const { kpis, anomalies, agents } = data
  const openAnomalies = anomalies.filter((a) => a.status === 'open' || a.status === 'blocked')

  return (
    <div className="space-y-6">
      {/* Risk banner */}
      <div className="flex items-center justify-between rounded-xl border border-red-600/40 bg-gradient-to-r from-red-600/15 to-transparent p-5">
        <div className="flex items-center gap-3">
          <ShieldAlert className="h-6 w-6 text-red-400" />
          <div>
            <p className="font-semibold text-zinc-100">
              {kpis.open_anomalies} anomalies detected · {fmtNaira(kpis.total_exposure)}/month at
              risk
            </p>
            <p className="text-sm text-zinc-500">
              August 2026 payroll scan · Sterling Distributors Ltd
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={runScan}
            disabled={scanning}
            className="bg-emerald-600 font-semibold hover:bg-emerald-500"
          >
            {scanning ? (
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            {scanning ? 'Scanning…' : 'Run Payroll Scan'}
          </Button>
          <a href={api.auditPacketUrl()} download>
            <Button variant="outline" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800">
              Download Exceptions Pack
            </Button>
          </a>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KPICard label="Employees" value={kpis.total_employees} icon={Users} sub="on payroll" />
        <KPICard
          label="Verified"
          value={`${kpis.verified_count}/${kpis.total_employees}`}
          icon={BadgeCheck}
          accent="emerald"
          sub={`${kpis.compliance_pct}% identity-verified`}
        />
        <KPICard
          label="Open Anomalies"
          value={kpis.open_anomalies}
          icon={AlertTriangle}
          accent={kpis.open_anomalies > 0 ? 'red' : 'emerald'}
          sub="require human decision"
        />
        <KPICard
          label="NCVS Compliance"
          value={`${kpis.compliance_pct}%`}
          accent="emerald"
          sub="credential verification mandate"
        />
      </div>

      {/* Agent fleet */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-500 mb-3">
          Agent Fleet
        </h2>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {agents.map((ag) => (
            <AgentCard key={ag.agent_id} agent={ag} />
          ))}
        </div>
      </div>

      {/* Anomaly queue — full width table */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-500 mb-3">
          Anomaly Queue ({openAnomalies.length} open · {anomalies.length} total)
        </h2>
        {anomalies.length === 0 ? (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-8 text-center text-zinc-500">
            No anomalies on record — run a payroll scan to analyze the August run.
          </div>
        ) : (
          <AnomalyTable anomalies={anomalies} onDecide={decide} />
        )}
      </div>
    </div>
  )
}
