// Login — instant demo login, one click, no fake delay.

import { Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function Login({ onLogin }: { onLogin: () => void }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-100">
      <div className="w-full max-w-sm rounded-2xl border border-zinc-800 bg-zinc-900/60 p-8">
        <div className="flex flex-col items-center text-center">
          <Shield className="h-10 w-10 text-emerald-400" />
          <h1 className="mt-4 text-xl font-bold">GhostGuard</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Payroll integrity for Sterling Distributors Ltd
          </p>
        </div>
        <div className="mt-6 space-y-3">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2.5">
            <div className="text-[10px] uppercase tracking-wider text-zinc-600">Email</div>
            <div className="text-sm text-zinc-300">hamzattiamiyu@gmail.com</div>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2.5">
            <div className="text-[10px] uppercase tracking-wider text-zinc-600">Role</div>
            <div className="text-sm text-zinc-300">HR / Payroll Administrator</div>
          </div>
          <Button
            onClick={onLogin}
            className="w-full bg-emerald-600 font-semibold hover:bg-emerald-500"
          >
            Sign in
          </Button>
          <p className="text-center text-[11px] text-zinc-600">
            Demo environment — Dojah sandbox · fictional data
          </p>
        </div>
      </div>
    </div>
  )
}
