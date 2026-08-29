// GhostGuard API types — mirrors backend Pydantic schemas (app/models/schemas.py)

export type LayerName = 'identity' | 'shared_attributes' | 'existence' | 'process' | 'cross_check'

export type Verdict = 'CLEAR' | 'FLAG' | 'BLOCK'

export type AuditVerdict = 'BLOCKED' | 'FLAGGED' | 'SEALED' | 'ESCALATED' | 'INFO'

export type AnomalyStatus = 'open' | 'explained' | 'escalated' | 'blocked'

export type AgentState = 'idle' | 'active' | 'armed' | 'error'

export interface LayerFinding {
  layer: LayerName
  signal: string
  description: string
  evidence: Record<string, unknown>
  points: number
  source: string
}

export interface Anomaly {
  anomaly_id: string
  employee_id: string
  employee_name: string
  run_id: string | null
  findings: LayerFinding[]
  total_score: number
  verdict: Verdict
  monthly_exposure: number
  explanation: string
  status: AnomalyStatus
  decided_by: string | null
  decided_at?: string | null
}

export interface AuditEvent {
  event_id: string
  timestamp: string
  event_type: string
  actor: string
  action: string
  target: string | null
  verdict: AuditVerdict | null
  detail: string | null
  payload_json?: string | null
  evidence_hash: string
  chain_hash: string
}

export interface AgentStatus {
  agent_id: string
  name: string
  state: AgentState
  tasks_completed: number
  tasks_failed: number
  last_run: string | null
  summary_metric: string | null
}

export interface DashboardKpis {
  total_employees: number
  verified_count: number
  open_anomalies: number
  compliance_pct: number
  total_exposure: number
}

export interface DashboardResponse {
  kpis: DashboardKpis
  anomalies: Anomaly[]
  agents: AgentStatus[]
}

export interface ScanResponse {
  run_id: string
  anomalies_found: number
  anomalies: Anomaly[]
}

export interface DefenseStep {
  step: string
  status: string // 'complete' | 'pass' | 'blocked' | 'match' | 'mismatch' | ...
  detail: string
}

export interface DefenseResponse {
  simulation: string
  steps: DefenseStep[]
  verdict: string
  details: Record<string, unknown>
}

export interface RedTeamAttack {
  id: string
  name: string
  description: string
  submitted: boolean
  caught: boolean
  caught_by: string[]
  expected_catch: string
  guardian_verdict: string
  threats_found: number
}

export interface RedTeamResponse {
  attacks: RedTeamAttack[]
  all_caught: boolean
  audit_sealed: boolean
}

export interface AuditTrailResponse {
  events: AuditEvent[]
  count: number
}

export interface AuditChainStatus {
  chain_valid: boolean
  events_count: number
  latest_hash: string
}

export interface ApprovalDecision {
  anomaly_id: string
  decision: 'block' | 'explain' | 'request_info'
  actor: string
  note: string
}

export interface ApprovalResult {
  success: boolean
  anomaly_id?: string
  new_status?: string
  decided_by?: string
  error?: string
}

export interface CsvUploadResult {
  success: boolean
  rows?: number
  category?: string
  error?: string
  threats?: string[]
  [key: string]: unknown
}

export interface OdooConnectResult {
  connected: boolean
  provider: string
  message: string
}

export interface OdooExpense {
  id?: number | string
  employee?: string
  description?: string
  amount?: number
  [key: string]: unknown
}

export interface OdooPollResult {
  expenses: OdooExpense[]
  count: number
}

export interface SchedulerConfig {
  enabled: boolean
  frequency: 'daily' | 'weekly' | 'monthly' | 'custom'
  custom_seconds: number | null
  notification_preference: 'full' | 'summary' | 'none'
  notification_email: string
  next_run: string | null
  last_run: string | null
  runs_completed: number
}

export interface Employee {
  employee_id: string
  full_name: string
  nin: string | null
  bvn: string | null
  bank_account: string | null
  bank_code: string | null
  phone: string | null
  address: string | null
  department: string
  position: string
  monthly_salary: number
  status: 'active' | 'terminated' | 'suspended'
  identity_verified: boolean
  verification_source: string | null
  [key: string]: unknown
}
