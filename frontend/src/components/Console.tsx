// Console — terminal-style step-by-step output for defense simulations.
// Adapted from the Kimi scaffold Console; resets whenever `runId` changes.

import { useEffect, useRef, useState } from 'react'
import { CheckCircle2, Loader2, ShieldAlert, ShieldCheck, XCircle } from 'lucide-react'
import type { DefenseStep } from '@/lib/types'

export interface ConsoleStep {
  text: string
  tone?: 'info' | 'ok' | 'warn' | 'bad'
  delay?: number
}

interface Props {
  steps: ConsoleStep[]
  runId: number // increment to restart the animation
  className?: string
}

/** Map backend DefenseStep status → console tone */
export function stepTone(status: string): ConsoleStep['tone'] {
  switch (status) {
    case 'pass':
    case 'match':
      return 'ok'
    case 'blocked':
    case 'mismatch':
      return 'bad'
    case 'warn':
      return 'warn'
    default:
      return 'info'
  }
}

export function defenseStepsToConsole(steps: DefenseStep[]): ConsoleStep[] {
  return steps.map((s) => ({
    text: `${s.step}${s.detail ? ` — ${s.detail}` : ''}`,
    tone: stepTone(s.status),
    delay: 650,
  }))
}

export default function Console({ steps, runId, className = '' }: Props) {
  const [visible, setVisible] = useState(0)
  const [done, setDone] = useState(false)
  const boxRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (runId === 0 || steps.length === 0) {
      setVisible(0)
      setDone(false)
      return
    }
    setVisible(0)
    setDone(false)
    let i = 0
    let timer: ReturnType<typeof setTimeout>
    const tick = () => {
      i += 1
      setVisible(i)
      if (i < steps.length) {
        timer = setTimeout(tick, steps[i]?.delay ?? 650)
      } else {
        setDone(true)
      }
    }
    timer = setTimeout(tick, steps[0]?.delay ?? 500)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId])

  useEffect(() => {
    boxRef.current?.scrollTo({ top: boxRef.current.scrollHeight, behavior: 'smooth' })
  }, [visible])

  const iconFor = (isLast: boolean, tone?: string) => {
    if (!done && isLast) return <Loader2 className="h-4 w-4 animate-spin text-zinc-400 shrink-0" />
    switch (tone) {
      case 'ok':
        return <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
      case 'warn':
        return <ShieldAlert className="h-4 w-4 text-amber-400 shrink-0" />
      case 'bad':
        return <XCircle className="h-4 w-4 text-red-400 shrink-0" />
      default:
        return <ShieldCheck className="h-4 w-4 text-zinc-500 shrink-0" />
    }
  }

  const colorFor = (tone?: string) => {
    switch (tone) {
      case 'ok':
        return 'text-emerald-300'
      case 'warn':
        return 'text-amber-300'
      case 'bad':
        return 'text-red-300'
      default:
        return 'text-zinc-300'
    }
  }

  return (
    <div
      ref={boxRef}
      className={`rounded-lg border border-zinc-800 bg-zinc-950 p-4 font-mono text-[13px] leading-6 max-h-64 overflow-y-auto ${className}`}
    >
      {steps.slice(0, visible).map((s, i) => (
        <div key={i} className="flex items-start gap-2.5 animate-in fade-in slide-in-from-left-1 duration-300">
          <span className="mt-1">{iconFor(i === visible - 1, s.tone)}</span>
          <span className={colorFor(s.tone)}>{s.text}</span>
        </div>
      ))}
      {visible === 0 && <span className="text-zinc-600">Awaiting agent run…</span>}
    </div>
  )
}
