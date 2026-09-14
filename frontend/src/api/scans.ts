import { api } from './client'
import type {
  AIAnalysisResponse,
  EndpointHistoryItem,
  Finding,
  PaginatedResponse,
  RegressionResponse,
  ScanCreateResponse,
  ScanDetail,
  ScanHistoryItem,
  SecurityScanResponse,
} from '../types'

function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export interface ScanListParams {
  page?: number
  page_size?: number
  status?: string
  risk_level?: string
}

export interface FindingListParams {
  page?: number
  page_size?: number
  severity?: string
  category?: string
  risk_level?: string
  min_risk_score?: number
}

export async function listScans(
  params: ScanListParams = {},
): Promise<PaginatedResponse<ScanHistoryItem>> {
  const { data } = await api.get<PaginatedResponse<ScanHistoryItem>>('/api/v1/scans', {
    params,
  })
  return data
}

export async function getScan(scanId: number): Promise<ScanDetail> {
  const { data } = await api.get<ScanDetail>(`/api/v1/scans/${scanId}`)
  return data
}

export async function createScan(file: File, name?: string): Promise<ScanCreateResponse> {
  const form = new FormData()
  form.append('file', file)
  if (name?.trim()) {
    form.append('name', name.trim())
  }
  const { data } = await api.post<ScanCreateResponse>('/api/v1/scans', form)
  return data
}

export async function deleteScan(scanId: number): Promise<void> {
  await api.delete(`/api/v1/scans/${scanId}`)
}

export async function runSecurityScan(scanId: number): Promise<SecurityScanResponse> {
  const { data } = await api.post<SecurityScanResponse>(
    `/api/v1/scans/${scanId}/security-scan`,
  )
  return data
}

export async function listEndpoints(
  scanId: number,
  page = 1,
  page_size = 50,
): Promise<PaginatedResponse<EndpointHistoryItem>> {
  const { data } = await api.get<PaginatedResponse<EndpointHistoryItem>>(
    `/api/v1/scans/${scanId}/endpoints`,
    { params: { page, page_size } },
  )
  return data
}

export async function listFindings(
  scanId: number,
  params: FindingListParams = {},
): Promise<PaginatedResponse<Finding>> {
  const { data } = await api.get<PaginatedResponse<Finding>>(
    `/api/v1/scans/${scanId}/findings`,
    { params },
  )
  return data
}

export async function getFindingById(
  scanId: number,
  findingId: number,
): Promise<Finding | null> {
  let page = 1
  let totalPages = 1

  while (page <= totalPages) {
    const response = await listFindings(scanId, { page, page_size: 100 })
    const match = response.items.find((item) => item.id === findingId)
    if (match) {
      return match
    }
    totalPages = response.total_pages
    page += 1
  }

  return null
}

export async function analyzeFinding(
  scanId: number,
  findingId: number,
  forceRefresh = false,
): Promise<AIAnalysisResponse> {
  const { data } = await api.post<AIAnalysisResponse>(
    `/api/v1/scans/${scanId}/findings/${findingId}/analyze`,
    null,
    { params: { force_refresh: forceRefresh } },
  )
  return data
}

export async function downloadScanReportPdf(scanId: number): Promise<void> {
  const response = await api.get(`/api/v1/scans/${scanId}/report/pdf`, {
    responseType: 'blob',
  })
  const blob = new Blob([response.data], { type: 'application/pdf' })
  triggerBlobDownload(blob, `security-report-${scanId}.pdf`)
}

export async function compareScans(
  scanId: number,
  baselineScanId: number,
): Promise<RegressionResponse> {
  const { data } = await api.get<RegressionResponse>(
    `/api/v1/scans/${scanId}/compare/${baselineScanId}`,
  )
  return data
}

export async function downloadComparisonReportPdf(
  scanId: number,
  baselineScanId: number,
): Promise<void> {
  const response = await api.get(
    `/api/v1/scans/${scanId}/compare/${baselineScanId}/report/pdf`,
    { responseType: 'blob' },
  )
  const blob = new Blob([response.data], { type: 'application/pdf' })
  triggerBlobDownload(blob, `comparison-report-${baselineScanId}-vs-${scanId}.pdf`)
}
