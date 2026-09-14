export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW'
export type ScanStatus = 'PENDING' | 'COMPLETED' | 'FAILED' | string

export interface User {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
}

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface SpecMetadataSummary {
  title?: string | null
  version?: string | null
  openapi_version?: string | null
  description?: string | null
}

export interface ScanSummary {
  endpoint_count: number
  finding_count: number
  critical: number
  high: number
  medium: number
  low: number
  info: number
  overall_risk_score: number
  risk_level: string
  ai_analysis_count: number
}

export interface ScanHistoryItem {
  id: number
  name: string
  status: ScanStatus
  created_at: string
  updated_at?: string | null
  completed_at?: string | null
  spec_metadata: SpecMetadataSummary
  endpoint_count: number
  finding_count: number
  risk_level?: string | null
  overall_risk_score?: number | null
}

export interface ScanCreateResponse {
  scan_id: number
  name: string
  status: string
}

export interface ScanDetail {
  id: number
  scan_id?: number | null
  name: string
  source_filename: string
  status: ScanStatus
  created_at: string
  updated_at?: string | null
  completed_at?: string | null
  specification_version?: string | null
  title?: string | null
  description?: string | null
  version?: string | null
  endpoint_count: number
  spec_metadata?: SpecMetadataSummary | Record<string, unknown> | null
  summary: ScanSummary
}

export interface EndpointHistoryItem {
  id: number
  method: string
  path: string
  summary?: string | null
  operation_id?: string | null
  finding_count: number
  security_defined: boolean
  security_requirements?: Record<string, unknown>[] | null
  tags: string[]
}

export interface FindingAIAnalysis {
  summary?: string | null
  why_it_matters?: string | null
  technical_reasoning?: string | null
  validation_guidance?: string | null
  remediation?: string | null
  priority?: string | null
  limitations?: string | null
  model?: string | null
  analyzed_at?: string | null
}

export interface Finding {
  id: number
  title: string
  severity: string
  category: string
  owasp_category?: string | null
  endpoint?: string | null
  evidence: string
  structured_evidence?: Record<string, unknown> | null
  confidence: string
  remediation: string
  risk_score: number
  risk_level: RiskLevel
  risk_factors?: Record<string, unknown> | null
  ai_analysis?: FindingAIAnalysis | null
  description?: string
  created_at?: string
}

export interface SecurityScanResponse {
  scan_id: number
  total_findings: number
  findings_count: number
  critical: number
  high: number
  medium: number
  low: number
  info: number
  overall_risk_score: number
  risk_level: RiskLevel
  findings: Finding[]
}

export interface AIAnalysisResponse {
  finding_id: number
  ai_analysis: {
    summary: string
    why_it_matters: string
    technical_reasoning: string
    validation_guidance: string
    remediation: string
    priority: RiskLevel
    limitations: string
  }
  model: string
  cached: boolean
  analyzed_at?: string | null
}

export interface ApiErrorBody {
  detail?: string | { msg?: string; loc?: unknown[] }[] | Record<string, unknown>
}

export interface RegressionFindingItem {
  id: number
  title: string
  category: string
  severity: string
  risk_score: number
  risk_level: string
  endpoint?: string | null
  method?: string | null
  path?: string | null
  fingerprint: string
}

export interface RegressionScanInfo {
  id: number
  name: string
  status: string
  overall_risk_score: number
  overall_risk_level: string
  finding_count: number
}

export interface RegressionResponse {
  baseline_scan: RegressionScanInfo
  current_scan: RegressionScanInfo
  baseline_risk_score: number
  current_risk_score: number
  risk_score_change: number
  baseline_risk_level: string
  current_risk_level: string
  new_findings: RegressionFindingItem[]
  resolved_findings: RegressionFindingItem[]
  persistent_findings: RegressionFindingItem[]
  new_critical_count: number
  resolved_critical_count: number
  posture: string
  summary: string
}
