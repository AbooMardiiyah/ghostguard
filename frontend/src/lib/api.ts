// GhostGuard API client — typed fetch wrapper for the FastAPI backend.

import type {
  Anomaly,
  ApprovalDecision,
  ApprovalResult,
  AuditChainStatus,
  AuditTrailResponse,
  CsvUploadResult,
  DashboardResponse,
  DefenseResponse,
  OdooConnectResult,
  OdooPollResult,
  RedTeamResponse,
  ScanResponse,
  SchedulerConfig,
} from './types'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  return res.json() as Promise<T>
}

function postForm<T>(path: string, data: Record<string, string>): Promise<T> {
  const form = new FormData()
  for (const [k, v] of Object.entries(data)) form.append(k, v)
  return request<T>(path, { method: 'POST', body: form })
}

export const api = {
  // Dashboard / Command Center
  dashboard: () => request<DashboardResponse>('/api/dashboard'),

  // Payroll
  scanPayroll: () => request<ScanResponse>('/api/payroll/scan', { method: 'POST' }),

  // Live Defense simulations
  defenseReconcile: () => request<DefenseResponse>('/api/defense/reconcile', { method: 'POST' }),
  defenseOnboardGhost: (fullName = 'Jane Smith', nin = '70123456789') =>
    postForm<DefenseResponse>('/api/defense/onboard-ghost', { full_name: fullName, nin }),
  defenseDeepfake: (transcript?: string) =>
    postForm<DefenseResponse>(
      '/api/defense/deepfake-approval',
      transcript ? { transcript } : {},
    ),
  defenseFakeReceipt: (file?: File, claimedAmount = 48500, claimedVat = 5000) => {
    const form = new FormData()
    if (file) form.append('receipt', file)
    form.append('claimed_amount', String(claimedAmount))
    form.append('claimed_vat', String(claimedVat))
    form.append('employee_id', 'EMP-040')
    return request<DefenseResponse>('/api/defense/fake-receipt', { method: 'POST', body: form })
  },

  // Red-Team
  runRedTeam: () => request<RedTeamResponse>('/api/redteam/run', { method: 'POST' }),

  // Audit
  auditTrail: () => request<AuditTrailResponse>('/api/audit'),
  auditVerify: () => request<AuditChainStatus>('/api/audit/verify'),
  auditPacketUrl: () => `${BASE}/api/audit/packet`,

  // Human gate
  decide: (decision: ApprovalDecision) =>
    request<ApprovalResult>('/api/approvals/decide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(decision),
    }),

  // Integrations
  uploadCsv: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<CsvUploadResult>('/api/integrations/csv/upload', { method: 'POST', body: form })
  },
  odooConnect: () => request<OdooConnectResult>('/api/integrations/odoo/connect', { method: 'POST' }),
  odooDisconnect: () => request<{ disconnected: boolean; message: string }>('/api/integrations/odoo/disconnect', { method: 'POST' }),
  odooPoll: () => request<OdooPollResult>('/api/integrations/odoo/poll', { method: 'POST' }),

  // Scheduler
  schedulerGet: () => request<SchedulerConfig>('/api/scheduler'),
  schedulerConfigure: (config: {
    frequency: string
    enabled: boolean
    custom_seconds?: number
    notification_preference?: string
    notification_email?: string
  }) => {
    const params = new URLSearchParams()
    params.set('frequency', config.frequency)
    params.set('enabled', String(config.enabled))
    if (config.custom_seconds != null) params.set('custom_seconds', String(config.custom_seconds))
    if (config.notification_preference) params.set('notification_preference', config.notification_preference)
    if (config.notification_email) params.set('notification_email', config.notification_email)
    return request<SchedulerConfig>(`/api/scheduler/configure?${params}`, { method: 'POST' })
  },
  schedulerRunNow: () =>
    request<{ triggered: boolean; scan_result: ScanResponse; schedule: SchedulerConfig }>(
      '/api/scheduler/run-now', { method: 'POST' },
    ),
  sendAnomalyEmail: (recipient: string, anomalies: Anomaly[]) =>
    request<{ sent: boolean }>('/api/scheduler/send-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        recipient,
        anomalies_json: JSON.stringify(anomalies),
      }),
    }),
}
