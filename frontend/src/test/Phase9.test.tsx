import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import type { ReactNode } from 'react'
import { AuthProvider } from '../context/AuthContext'
import { ToastProvider } from '../context/ToastContext'
import { ScanDetailPage } from '../pages/ScanDetailPage'
import { ComparePage } from '../pages/ComparePage'
import {
  PostureBanner,
  RegressionFindingList,
} from '../components/RegressionSections'
import type { RegressionFindingItem, RegressionResponse } from '../types'

vi.mock('../api/auth', () => ({
  loginUser: vi.fn(),
  registerUser: vi.fn(),
  getCurrentUser: vi.fn(),
}))

vi.mock('../api/scans', () => ({
  getScan: vi.fn(),
  runSecurityScan: vi.fn(),
  downloadScanReportPdf: vi.fn(),
  listScans: vi.fn(),
  listFindings: vi.fn(),
  compareScans: vi.fn(),
  downloadComparisonReportPdf: vi.fn(),
}))

import { getCurrentUser } from '../api/auth'
import {
  compareScans,
  downloadScanReportPdf,
  getScan,
  listFindings,
  listScans,
} from '../api/scans'

const mockedGetCurrentUser = vi.mocked(getCurrentUser)
const mockedGetScan = vi.mocked(getScan)
const mockedDownloadReport = vi.mocked(downloadScanReportPdf)
const mockedListScans = vi.mocked(listScans)
const mockedListFindings = vi.mocked(listFindings)
const mockedCompare = vi.mocked(compareScans)

function renderWithAuth(ui: ReactNode, initialEntries = ['/']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AuthProvider>
        <ToastProvider>{ui}</ToastProvider>
      </AuthProvider>
    </MemoryRouter>,
  )
}

const sampleFinding = (overrides: Partial<RegressionFindingItem> = {}): RegressionFindingItem => ({
  id: 1,
  title: 'Missing authentication',
  category: 'authentication',
  severity: 'HIGH',
  risk_score: 80,
  risk_level: 'HIGH',
  endpoint: 'GET /users',
  method: 'GET',
  path: '/users',
  fingerprint: 'authentication|missing authentication|GET|/users',
  ...overrides,
})

describe('report download action', () => {
  beforeEach(() => {
    localStorage.setItem('aasa_access_token', 'token')
    mockedGetCurrentUser.mockResolvedValue({
      id: 1,
      username: 'alice',
      email: 'alice@example.com',
      role: 'user',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    })
    mockedGetScan.mockResolvedValue({
      id: 9,
      name: 'Demo scan',
      source_filename: 'demo.yaml',
      status: 'COMPLETED',
      created_at: '2026-09-01T00:00:00Z',
      endpoint_count: 3,
      summary: {
        endpoint_count: 3,
        finding_count: 2,
        critical: 0,
        high: 1,
        medium: 1,
        low: 0,
        info: 0,
        overall_risk_score: 75,
        risk_level: 'HIGH',
        ai_analysis_count: 0,
      },
    })
    mockedListFindings.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 100,
      total: 0,
      total_pages: 0,
    })
  })

  it('triggers PDF download from scan detail', async () => {
    const user = userEvent.setup()
    mockedDownloadReport.mockResolvedValue(undefined)

    renderWithAuth(
      <Routes>
        <Route path="/scans/:scanId" element={<ScanDetailPage />} />
      </Routes>,
      ['/scans/9'],
    )

    await screen.findByText('Demo scan')
    await user.click(screen.getByRole('button', { name: /download security report/i }))

    await waitFor(() => {
      expect(mockedDownloadReport).toHaveBeenCalledWith(9)
      expect(screen.getByText(/security report download started/i)).toBeInTheDocument()
    })
  })
})

describe('comparison page', () => {
  beforeEach(() => {
    localStorage.setItem('aasa_access_token', 'token')
    mockedGetCurrentUser.mockResolvedValue({
      id: 1,
      username: 'alice',
      email: 'alice@example.com',
      role: 'user',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    })
    mockedListScans.mockResolvedValue({
      items: [
        {
          id: 2,
          name: 'Baseline',
          status: 'COMPLETED',
          created_at: '2026-09-01T00:00:00Z',
          spec_metadata: {},
          endpoint_count: 3,
          finding_count: 4,
          risk_level: 'HIGH',
          overall_risk_score: 82,
        },
      ],
      page: 1,
      page_size: 100,
      total: 1,
      total_pages: 1,
    })
  })

  it('loads comparison and shows risk change sections', async () => {
    const comparison: RegressionResponse = {
      baseline_scan: {
        id: 2,
        name: 'Baseline',
        status: 'COMPLETED',
        overall_risk_score: 82,
        overall_risk_level: 'HIGH',
        finding_count: 4,
      },
      current_scan: {
        id: 5,
        name: 'Current',
        status: 'COMPLETED',
        overall_risk_score: 61,
        overall_risk_level: 'MEDIUM',
        finding_count: 3,
      },
      baseline_risk_score: 82,
      current_risk_score: 61,
      risk_score_change: -21,
      baseline_risk_level: 'HIGH',
      current_risk_level: 'MEDIUM',
      new_findings: [sampleFinding({ id: 10, title: 'New injection risk' })],
      resolved_findings: [sampleFinding({ id: 11, title: 'Old auth gap' })],
      persistent_findings: [sampleFinding({ id: 12, title: 'Still missing rate limit' })],
      new_critical_count: 0,
      resolved_critical_count: 0,
      posture: 'IMPROVED',
      summary:
        'Security Posture Improved. 1 finding(s) resolved, 1 new finding(s) detected, 1 finding(s) remain persistent. Risk score decreased by 21 points.',
    }
    mockedCompare.mockResolvedValue(comparison)

    renderWithAuth(
      <Routes>
        <Route path="/scans/:scanId/compare/:baselineScanId" element={<ComparePage />} />
      </Routes>,
      ['/scans/5/compare/2'],
    )

    await waitFor(() => {
      expect(screen.getByText('IMPROVED')).toBeInTheDocument()
      expect(screen.getByText('-21')).toBeInTheDocument()
      expect(screen.getByText('New injection risk')).toBeInTheDocument()
      expect(screen.getByText('Old auth gap')).toBeInTheDocument()
      expect(screen.getByText('Still missing rate limit')).toBeInTheDocument()
    })
  })

  it('shows loading then error state', async () => {
    mockedCompare.mockRejectedValue(new Error('Unable to compare scans.'))

    renderWithAuth(
      <Routes>
        <Route path="/scans/:scanId/compare/:baselineScanId" element={<ComparePage />} />
      </Routes>,
      ['/scans/5/compare/2'],
    )

    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText(/comparison error/i)).toBeInTheDocument()
      expect(screen.getByText(/unable to compare scans/i)).toBeInTheDocument()
    })
  })
})

describe('regression rendering helpers', () => {
  it('renders posture and finding buckets', () => {
    render(
      <>
        <PostureBanner posture="IMPROVED" summary="Risk decreased." />
        <RegressionFindingList
          title="New findings"
          kind="new"
          findings={[sampleFinding({ title: 'Fresh issue' })]}
          emptyLabel="none"
        />
        <RegressionFindingList
          title="Resolved findings"
          kind="resolved"
          findings={[sampleFinding({ id: 2, title: 'Fixed issue' })]}
          emptyLabel="none"
        />
        <RegressionFindingList
          title="Persistent findings"
          kind="persistent"
          findings={[sampleFinding({ id: 3, title: 'Ongoing issue' })]}
          emptyLabel="none"
        />
      </>,
    )

    expect(screen.getByText('IMPROVED')).toBeInTheDocument()
    expect(screen.getByText('Fresh issue')).toBeInTheDocument()
    expect(screen.getByText('Fixed issue')).toBeInTheDocument()
    expect(screen.getByText('Ongoing issue')).toBeInTheDocument()
  })
})
