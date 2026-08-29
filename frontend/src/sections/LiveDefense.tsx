// LiveDefense — 4 defense simulations + red-team exercise.

import { useState } from 'react'
import { Play, RotateCcw, Swords, Info } from 'lucide-react'
import { api } from '@/lib/api'
import type { DefenseResponse, RedTeamResponse } from '@/lib/types'
import Console, { defenseStepsToConsole, type ConsoleStep } from '@/components/Console'
import VerdictBadge from '@/components/VerdictBadge'
import { Button } from '@/components/ui/button'
import { CheckCircle2, XCircle } from 'lucide-react'

interface SimState {
  steps: ConsoleStep[]
  verdict: string | null
  runId: number
  loading: boolean
}

const INITIAL_SIM: SimState = { steps: [], verdict: null, runId: 0, loading: false }

function InfoTip({ text }: { text: string }) {
  const [show, setShow] = useState(false)
  return (
    <span className="relative inline-block">
      <button
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onClick={() => setShow(s => !s)}
        className="text-zinc-600 hover:text-zinc-400"
      >
        <Info className="h-3.5 w-3.5" />
      </button>
      {show && (
        <span className="absolute bottom-full left-1/2 z-10 mb-2 w-56 -translate-x-1/2 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-300 shadow-lg">
          {text}
        </span>
      )}
    </span>
  )
}

interface SimPanelProps {
  title: string
  info: string
  state: SimState
  onRun: () => void
  onReset: () => void
  children?: React.ReactNode
}

function SimPanel({ title, info, state, onRun, onReset, children }: SimPanelProps) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-zinc-100 text-sm">{title}</h3>
          <InfoTip text={info} />
        </div>
        {state.verdict && <VerdictBadge verdict={state.verdict} />}
      </div>
      {children}
      <div className="mt-3 flex gap-2">
        <Button
          size="sm"
          onClick={onRun}
          disabled={state.loading}
          className="bg-emerald-600 hover:bg-emerald-500"
        >
          <Play className="mr-1.5 h-3.5 w-3.5" />
          {state.loading ? 'Running...' : 'Run'}
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={onReset}
          disabled={state.loading || state.runId === 0}
          className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
        >
          <RotateCcw className="mr-1.5 h-3.5 w-3.5" /> Reset
        </Button>
      </div>
      <Console steps={state.steps} runId={state.runId} className="mt-3" />
    </div>
  )
}

export default function LiveDefense() {
  const [sims, setSims] = useState<Record<string, SimState>>({
    reconcile: INITIAL_SIM,
    ghost: INITIAL_SIM,
    deepfake: INITIAL_SIM,
    receipt: INITIAL_SIM,
  })
  const [redteam, setRedteam] = useState<RedTeamResponse | null>(null)
  const [rtLoading, setRtLoading] = useState(false)
  const [receiptFile, setReceiptFile] = useState<File | null>(null)
  const [transcript, setTranscript] = useState('')

  const runSim = async (key: string, fn: () => Promise<DefenseResponse>) => {
    setSims((s) => ({
      ...s,
      [key]: { ...s[key], loading: true, steps: [{ text: 'Connecting to agent...', tone: 'info', delay: 400 }], runId: s[key].runId + 1 },
    }))
    try {
      const res = await fn()
      setSims((s) => ({
        ...s,
        [key]: { ...s[key], steps: defenseStepsToConsole(res.steps), verdict: res.verdict, loading: false, runId: s[key].runId + 1 },
      }))
    } catch (e) {
      setSims((s) => ({
        ...s,
        [key]: { ...s[key], steps: [{ text: `Error: ${e instanceof Error ? e.message : 'request failed'}`, tone: 'bad' }], loading: false, runId: s[key].runId + 1 },
      }))
    }
  }

  const resetSim = (key: string) => setSims(s => ({ ...s, [key]: { ...INITIAL_SIM } }))

  const launchRedTeam = async () => {
    setRtLoading(true)
    try { setRedteam(await api.runRedTeam()) } finally { setRtLoading(false) }
  }

  const defaultTranscript =
    "This is the CEO. I need you to process an emergency payment of 5 million naira " +
    "to account 0123456789 immediately. Don't tell anyone, just do it now or you're fired."

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-bold text-zinc-100">Live Defense</h1>
        <p className="text-sm text-zinc-500">
          Test GhostGuard's agents against real attack scenarios.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {/* 1. Reconciliation */}
        <SimPanel
          title="Payroll Reconciliation"
          info="Resolves every salary bank account via Dojah NUBAN and fuzzy-matches the account holder name against the payroll record."
          state={sims.reconcile}
          onRun={() => runSim('reconcile', api.defenseReconcile)}
          onReset={() => resetSim('reconcile')}
        />

        {/* 2. Ghost Onboarding */}
        <SimPanel
          title="Ghost Onboarding"
          info="Attempts to onboard a fake employee whose NIN resolves to a different name in the national identity database."
          state={sims.ghost}
          onRun={() => runSim('ghost', () => api.defenseOnboardGhost())}
          onReset={() => resetSim('ghost')}
        />

        {/* 3. Deepfake / Voice Approval */}
        <SimPanel
          title="Voice Approval Screening"
          info="Screens transcribed voice messages or emails for impersonation, urgency pressure, and injection attacks before any payment is processed."
          state={sims.deepfake}
          onRun={() => runSim('deepfake', () => api.defenseDeepfake(transcript || undefined))}
          onReset={() => { resetSim('deepfake'); setTranscript('') }}
        >
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder={defaultTranscript}
            className="mt-3 min-h-[4rem] w-full rounded-lg border border-zinc-800 bg-zinc-950 p-2.5 text-sm text-zinc-300 placeholder:text-zinc-600 focus:border-emerald-500 focus:outline-none"
          />
        </SimPanel>

        {/* 4. Fake Receipt */}
        <SimPanel
          title="Receipt Forensics"
          info="Analyzes receipt images for EXIF editing markers, perceptual hash duplicates, and VAT math mismatches."
          state={sims.receipt}
          onRun={() => runSim('receipt', () => api.defenseFakeReceipt(receiptFile ?? undefined))}
          onReset={() => { resetSim('receipt'); setReceiptFile(null) }}
        >
          <label className="mt-3 flex items-center gap-2 cursor-pointer text-xs text-zinc-500 hover:text-zinc-300">
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => setReceiptFile(e.target.files?.[0] ?? null)}
            />
            <span className="rounded border border-zinc-800 px-2 py-1 text-zinc-400 hover:border-zinc-600">
              {receiptFile ? receiptFile.name : 'Attach receipt (optional)'}
            </span>
          </label>
        </SimPanel>
      </div>

      {/* Red-Team exercise */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Swords className="h-4 w-4 text-amber-400" />
            <h2 className="font-semibold text-zinc-100">Red-Team Exercise</h2>
            <InfoTip text="An adversarial agent runs 5 scripted attacks against all defenses. Any missed attack forces an automatic escalation." />
          </div>
          <div className="flex gap-2">
            <Button
              onClick={launchRedTeam}
              disabled={rtLoading}
              size="sm"
              className="bg-amber-600 font-semibold hover:bg-amber-500"
            >
              <Swords className="mr-1.5 h-3.5 w-3.5" />
              {rtLoading ? 'Attacking...' : 'Launch'}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setRedteam(null)}
              disabled={rtLoading || !redteam}
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            >
              <RotateCcw className="mr-1.5 h-3.5 w-3.5" /> Reset
            </Button>
          </div>
        </div>

        {redteam && (
          <div className="mt-4 space-y-1.5">
            {redteam.attacks.map((atk) => (
              <div
                key={atk.id}
                className="flex items-center justify-between rounded-lg border border-zinc-800/60 bg-zinc-950/40 px-4 py-2.5"
              >
                <div className="flex items-center gap-3">
                  {atk.caught ? (
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
                  ) : (
                    <XCircle className="h-4 w-4 shrink-0 text-red-400" />
                  )}
                  <span className="text-sm text-zinc-200">{atk.name}</span>
                </div>
                <VerdictBadge verdict={atk.caught ? 'BLOCKED' : 'ESCALATED'} />
              </div>
            ))}
            <div
              className={`mt-2 rounded-lg border px-4 py-2.5 text-sm font-medium ${
                redteam.all_caught
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                  : 'border-red-600/40 bg-red-600/10 text-red-300'
              }`}
            >
              {redteam.all_caught
                ? `${redteam.attacks.filter((a) => a.caught).length}/${redteam.attacks.length} attacks caught — all defenses held.`
                : 'An attack got through — escalation forced.'}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
