// Scheduler — configure automated scans with email notifications.

import { useCallback, useEffect, useState } from 'react'
import { Clock, Play, Save, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'
import { fmtDateTime } from '@/lib/format'
import { Button } from '@/components/ui/button'

type Frequency = 'daily' | 'weekly' | 'monthly' | 'custom'
type NotifPref = 'full' | 'summary' | 'none'

export default function Scheduler() {
  const [frequency, setFrequency] = useState<Frequency>('monthly')
  const [enabled, setEnabled] = useState(false)
  const [customSeconds, setCustomSeconds] = useState(30)
  const [notifPref, setNotifPref] = useState<NotifPref>('none')
  const [notifEmail, setNotifEmail] = useState('')

  const [lastRun, setLastRun] = useState<string | null>(null)
  const [nextRun, setNextRun] = useState<string | null>(null)
  const [runsCompleted, setRunsCompleted] = useState(0)
  const [isActive, setIsActive] = useState(false)

  const [saving, setSaving] = useState(false)
  const [running, setRunning] = useState(false)
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null)

  const loadConfig = useCallback(async () => {
    try {
      const cfg = await api.schedulerGet()
      setFrequency(cfg.frequency)
      setEnabled(cfg.enabled)
      setIsActive(cfg.enabled)
      if (cfg.custom_seconds) setCustomSeconds(cfg.custom_seconds)
      setNotifPref(cfg.notification_preference)
      setNotifEmail(cfg.notification_email)
      setLastRun(cfg.last_run)
      setNextRun(cfg.next_run)
      setRunsCompleted(cfg.runs_completed)
    } catch {
      // backend may not be running yet
    }
  }, [])

  useEffect(() => { loadConfig() }, [loadConfig])

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)
    try {
      const cfg = await api.schedulerConfigure({
        frequency,
        enabled,
        custom_seconds: frequency === 'custom' ? customSeconds : undefined,
        notification_preference: notifPref,
        notification_email: notifEmail,
      })
      setIsActive(cfg.enabled)
      setNextRun(cfg.next_run)
      setLastRun(cfg.last_run)
      setRunsCompleted(cfg.runs_completed)
      setMessage({ text: enabled ? 'Scheduler activated' : 'Scheduler stopped', ok: true })
    } catch (e) {
      setMessage({ text: e instanceof Error ? e.message : 'Failed to save', ok: false })
    } finally {
      setSaving(false)
    }
  }

  const handleRunNow = async () => {
    setRunning(true)
    setMessage(null)
    try {
      const res = await api.schedulerRunNow()
      setLastRun(res.schedule.last_run)
      setRunsCompleted(res.schedule.runs_completed)
      const count = res.scan_result.anomalies_found
      setMessage({ text: `Scan complete — ${count} anomal${count === 1 ? 'y' : 'ies'} found`, ok: true })
    } catch (e) {
      setMessage({ text: e instanceof Error ? e.message : 'Scan failed', ok: false })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-bold text-zinc-100">Scheduler</h1>
        <p className="text-sm text-zinc-500">
          Configure automated payroll scans with optional email notifications.
        </p>
      </div>

      {message && (
        <div className={`rounded-lg border px-4 py-2.5 text-sm ${
          message.ok
            ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
            : 'border-red-600/40 bg-red-600/10 text-red-300'
        }`}>
          {message.text}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Configuration card */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
          <h2 className="flex items-center gap-2 font-semibold text-zinc-100 text-sm">
            <Clock className="h-4 w-4 text-emerald-400" /> Schedule Configuration
          </h2>

          {/* Enable toggle */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-zinc-300">Enable automated scans</span>
            <button
              onClick={() => setEnabled(!enabled)}
              className={`relative h-6 w-11 rounded-full transition-colors ${enabled ? 'bg-emerald-600' : 'bg-zinc-700'}`}
            >
              <span className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform ${enabled ? 'translate-x-5' : ''}`} />
            </button>
          </div>

          {/* Frequency */}
          <div>
            <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Frequency</label>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value as Frequency)}
              className="mt-1.5 w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-emerald-500 focus:outline-none"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="custom">Custom Interval</option>
            </select>
          </div>

          {/* Custom seconds */}
          {frequency === 'custom' && (
            <div>
              <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Interval (seconds)</label>
              <input
                type="number"
                min={10}
                value={customSeconds}
                onChange={(e) => setCustomSeconds(Number(e.target.value))}
                className="mt-1.5 w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-emerald-500 focus:outline-none"
              />
            </div>
          )}

          {/* Notification preference */}
          <div>
            <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Email Notification</label>
            <select
              value={notifPref}
              onChange={(e) => setNotifPref(e.target.value as NotifPref)}
              className="mt-1.5 w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-emerald-500 focus:outline-none"
            >
              <option value="none">No email</option>
              <option value="summary">Summary email (KPIs + top anomalies)</option>
              <option value="full">Full report (LLM summary + PDF attachment)</option>
            </select>
          </div>

          {/* Recipient email */}
          {notifPref !== 'none' && (
            <div>
              <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Recipient Email</label>
              <input
                type="email"
                value={notifEmail}
                onChange={(e) => setNotifEmail(e.target.value)}
                placeholder="auditor@company.com"
                className="mt-1.5 w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 placeholder:text-zinc-600 focus:border-emerald-500 focus:outline-none"
              />
            </div>
          )}

          <Button
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-emerald-600 hover:bg-emerald-500"
          >
            {saving ? <RefreshCw className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <Save className="mr-1.5 h-3.5 w-3.5" />}
            {saving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </div>

        {/* Status card */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
          <h2 className="flex items-center gap-2 font-semibold text-zinc-100 text-sm">
            <RefreshCw className="h-4 w-4 text-emerald-400" /> Schedule Status
          </h2>

          {/* Active indicator */}
          <div className="flex items-center gap-2.5">
            <span className={`h-2.5 w-2.5 rounded-full ${isActive ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'}`} />
            <span className={`text-sm font-medium ${isActive ? 'text-emerald-400' : 'text-zinc-500'}`}>
              {isActive ? 'Active' : 'Inactive'}
            </span>
          </div>

          {/* Stats */}
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Frequency</span>
              <span className="text-zinc-300 font-medium capitalize">
                {frequency === 'custom' ? `Every ${customSeconds}s` : frequency}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Notifications</span>
              <span className="text-zinc-300 font-medium capitalize">
                {notifPref === 'none' ? 'Off' : notifPref === 'summary' ? 'Summary' : 'Full Report'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Last run</span>
              <span className="text-zinc-300 font-medium">
                {lastRun ? fmtDateTime(lastRun) : 'Never'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Next run</span>
              <span className="text-zinc-300 font-medium">
                {isActive && nextRun ? fmtDateTime(nextRun) : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-zinc-500">Runs completed</span>
              <span className="text-zinc-300 font-medium">{runsCompleted}</span>
            </div>
          </div>

          <Button
            onClick={handleRunNow}
            disabled={running}
            variant="outline"
            className="w-full border-zinc-700 text-zinc-300 hover:bg-zinc-800"
          >
            {running ? <RefreshCw className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <Play className="mr-1.5 h-3.5 w-3.5" />}
            {running ? 'Scanning...' : 'Run Now'}
          </Button>
        </div>
      </div>
    </div>
  )
}
