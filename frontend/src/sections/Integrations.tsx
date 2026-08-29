// Integrations — CSV upload, Dojah identity, Odoo ERP connector.

import { useEffect, useRef, useState } from 'react'
import { FileUp, Landmark, Plug, RefreshCw, CheckCircle2, Unplug, Download } from 'lucide-react'
import { api } from '@/lib/api'
import type { CsvUploadResult } from '@/lib/types'
import { Button } from '@/components/ui/button'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export default function Integrations() {
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<CsvUploadResult | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const [odooConnected, setOdooConnected] = useState(false)
  const [odooMessage, setOdooMessage] = useState<string | null>(null)
  const [odooEmployees, setOdooEmployees] = useState<number | null>(null)
  const [odooBusy, setOdooBusy] = useState(false)

  const doUpload = async (file: File) => {
    setUploading(true)
    setUploadResult(null)
    try {
      setUploadResult(await api.uploadCsv(file))
    } catch (e) {
      setUploadResult({ success: false, error: e instanceof Error ? e.message : 'Upload failed' })
    } finally {
      setUploading(false)
    }
  }

  const connectOdoo = async () => {
    setOdooBusy(true)
    try {
      const conn = await api.odooConnect() as unknown as Record<string, unknown>
      if (conn.connected) {
        setOdooConnected(true)
        setOdooMessage(conn.message as string)
        setOdooEmployees((conn.employee_count as number) ?? 0)
      } else {
        setOdooConnected(false)
        setOdooMessage((conn.error as string) ?? 'Connection failed')
      }
    } catch {
      setOdooConnected(false)
      setOdooMessage('Connection failed')
    } finally {
      setOdooBusy(false)
    }
  }

  const disconnectOdoo = async () => {
    setOdooBusy(true)
    try {
      await api.odooDisconnect()
      setOdooConnected(false)
      setOdooMessage(null)
      setOdooEmployees(null)
    } catch {
      // still disconnect visually
      setOdooConnected(false)
    } finally {
      setOdooBusy(false)
    }
  }

  // Auto-connect on mount
  useEffect(() => { connectOdoo() }, [])

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-bold text-zinc-100">Integrations</h1>
        <p className="text-sm text-zinc-500">
          Connect your payroll data sources to GhostGuard.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* CSV Upload */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
          <h2 className="flex items-center gap-2 font-semibold text-zinc-100 text-sm">
            <FileUp className="h-4 w-4 text-emerald-400" /> CSV Upload
          </h2>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files?.[0]; if (f) doUpload(f) }}
            onClick={() => fileRef.current?.click()}
            className={`mt-3 cursor-pointer rounded-lg border-2 border-dashed p-5 text-center transition-colors ${
              dragOver ? 'border-emerald-500 bg-emerald-500/5' : 'border-zinc-800 hover:border-zinc-700'
            }`}
          >
            <FileUp className="mx-auto h-6 w-6 text-zinc-600" />
            <p className="mt-1.5 text-sm text-zinc-400">
              {uploading ? 'Scanning & importing...' : 'Drop CSV or click to browse'}
            </p>
            <p className="mt-1 text-[11px] text-zinc-600">
              payroll_register · hr_register · attendance_log
            </p>
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) doUpload(f); e.target.value = '' }}
            />
          </div>
          <a
            href={`${BASE}/api/integrations/csv/sample`}
            download
            className="mt-2 flex items-center gap-1.5 text-[11px] text-zinc-500 hover:text-emerald-400 transition-colors"
          >
            <Download className="h-3 w-3" /> Download sample CSV
          </a>
          {uploadResult && (
            <div className={`mt-2 rounded-lg border px-3 py-2 text-sm ${
              uploadResult.success !== false
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                : 'border-red-600/40 bg-red-600/10 text-red-300'
            }`}>
              {uploadResult.success !== false
                ? `Imported ${uploadResult.rows ?? 0} rows (${uploadResult.category ?? 'auto-detected'})`
                : `${uploadResult.error ?? 'Import failed'}`}
            </div>
          )}
        </div>

        {/* Dojah */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
          <h2 className="flex items-center gap-2 font-semibold text-zinc-100 text-sm">
            <Landmark className="h-4 w-4 text-emerald-400" /> Identity Verification
          </h2>
          <p className="mt-1.5 text-xs text-zinc-500">Powered by Dojah</p>

          <div className="mt-3 space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-sm text-zinc-300">NIN Verification</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-sm text-zinc-300">BVN Verification</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-sm text-zinc-300">NUBAN Account Resolution</span>
            </div>
          </div>

          <div className="mt-3 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-emerald-400">Connected — Sandbox</span>
          </div>
        </div>

        {/* Odoo */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
          <h2 className="flex items-center gap-2 font-semibold text-zinc-100 text-sm">
            <Plug className="h-4 w-4 text-emerald-400" /> Odoo ERP
          </h2>
          <p className="mt-1.5 text-xs text-zinc-500">Employee and payroll data via JSON-RPC</p>

          <div className="mt-3 flex gap-2">
            {odooConnected ? (
              <>
                <Button
                  onClick={connectOdoo}
                  disabled={odooBusy}
                  size="sm"
                  className="bg-emerald-600 hover:bg-emerald-500"
                >
                  {odooBusy ? <RefreshCw className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="mr-1.5 h-3.5 w-3.5" />}
                  {odooBusy ? 'Syncing...' : 'Re-sync'}
                </Button>
                <Button
                  onClick={disconnectOdoo}
                  size="sm"
                  variant="outline"
                  className="border-zinc-700 text-zinc-400 hover:text-red-400 hover:border-red-600/40"
                >
                  <Unplug className="mr-1.5 h-3.5 w-3.5" /> Disconnect
                </Button>
              </>
            ) : (
              <Button
                onClick={connectOdoo}
                disabled={odooBusy}
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-500"
              >
                {odooBusy ? <RefreshCw className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <Plug className="mr-1.5 h-3.5 w-3.5" />}
                {odooBusy ? 'Connecting...' : 'Connect & Sync'}
              </Button>
            )}
          </div>

          <div className="mt-3">
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${odooConnected ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'}`} />
              <span className={`text-xs ${odooConnected ? 'text-emerald-400' : 'text-zinc-500'}`}>
                {odooConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            {odooConnected && odooEmployees != null && (
              <div className="mt-2">
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-500">Employees synced</span>
                  <span className="text-zinc-300 font-medium">{odooEmployees}</span>
                </div>
              </div>
            )}
            {!odooConnected && odooMessage && (
              <p className="mt-1 text-xs text-red-400">{odooMessage}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
