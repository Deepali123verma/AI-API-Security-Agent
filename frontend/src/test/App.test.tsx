import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import type { ReactNode } from 'react'
import { AuthProvider } from '../context/AuthContext'
import { ProtectedRoute } from '../components/ProtectedRoute'
import { LoginPage } from '../pages/LoginPage'
import { SeverityBadge } from '../components/Badges'
import { ScanTable } from '../components/ScanTable'
import { FindingDetailPage } from '../pages/FindingDetailPage'
import { getErrorMessage, isAiUnavailable } from '../utils/errors'
import { AxiosError } from 'axios'
import type { Finding, ScanHistoryItem } from '../types'

vi.mock('../api/auth', () => ({
  loginUser: vi.fn(),
  registerUser: vi.fn(),
  getCurrentUser: vi.fn(),
}))

vi.mock('../api/scans', () => ({
  getFindingById: vi.fn(),
  analyzeFinding: vi.fn(),
}))

import { getCurrentUser, loginUser } from '../api/auth'
import { analyzeFinding, getFindingById } from '../api/scans'

const mockedLogin = vi.mocked(loginUser)
const mockedGetCurrentUser = vi.mocked(getCurrentUser)
const mockedGetFinding = vi.mocked(getFindingById)
const mockedAnalyze = vi.mocked(analyzeFinding)

function renderWithAuth(ui: ReactNode, initialEntries = ['/']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>,
  )
}

describe('login flow', () => {
  beforeEach(() => {
    localStorage.clear()
    mockedGetCurrentUser.mockRejectedValue(new Error('no session'))
  })

  it('stores token and redirects after successful login', async () => {
    const user = userEvent.setup()
    mockedLogin.mockResolvedValue({ access_token: 'test-token', token_type: 'bearer' })
    mockedGetCurrentUser.mockResolvedValue({
      id: 1,
      username: 'alice',
      email: 'alice@example.com',
      role: 'user',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    })

    renderWithAuth(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<div>Dashboard ready</div>} />
      </Routes>,
      ['/login'],
    )

    await user.type(screen.getByLabelText(/username/i), 'alice')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(localStorage.getItem('aasa_access_token')).toBe('test-token')
      expect(screen.getByText('Dashboard ready')).toBeInTheDocument()
    })
  })
})

describe('protected route', () => {
  beforeEach(() => {
    localStorage.clear()
    mockedGetCurrentUser.mockRejectedValue(new Error('no session'))
  })

  it('redirects unauthenticated users to login', async () => {
    renderWithAuth(
      <Routes>
        <Route path="/login" element={<div>Login screen</div>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<div>Secret dashboard</div>} />
        </Route>
      </Routes>,
      ['/dashboard'],
    )

    await waitFor(() => {
      expect(screen.getByText('Login screen')).toBeInTheDocument()
    })
    expect(screen.queryByText('Secret dashboard')).not.toBeInTheDocument()
  })
})

describe('scan history rendering', () => {
  it('renders scan rows with status and risk', () => {
    const scans: ScanHistoryItem[] = [
      {
        id: 7,
        name: 'Payments API',
        status: 'COMPLETED',
        created_at: '2026-09-01T12:00:00Z',
        spec_metadata: { title: 'Payments' },
        endpoint_count: 12,
        finding_count: 4,
        risk_level: 'HIGH',
        overall_risk_score: 82,
      },
    ]

    render(
      <MemoryRouter>
        <ScanTable scans={scans} />
      </MemoryRouter>,
    )

    expect(screen.getAllByText('Payments API').length).toBeGreaterThan(0)
    expect(screen.getAllByText('COMPLETED').length).toBeGreaterThan(0)
    expect(screen.getAllByText('HIGH').length).toBeGreaterThan(0)
    expect(screen.getAllByText('82').length).toBeGreaterThan(0)
  })
})

describe('severity display', () => {
  it('shows severity badge text', () => {
    render(<SeverityBadge value="critical" />)
    expect(screen.getByText('CRITICAL')).toBeInTheDocument()
  })
})

describe('AI analysis states', () => {
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
  })

  it('shows loading then success for Analyze with AI', async () => {
    const user = userEvent.setup()
    const finding: Finding = {
      id: 3,
      title: 'Missing auth',
      severity: 'HIGH',
      category: 'authentication',
      evidence: 'No security defined',
      confidence: 'HIGH',
      remediation: 'Add auth',
      risk_score: 80,
      risk_level: 'HIGH',
      ai_analysis: null,
    }

    mockedGetFinding.mockResolvedValue(finding)
    let resolveAnalyze: (value: unknown) => void = () => undefined
    mockedAnalyze.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveAnalyze = resolve
        }) as ReturnType<typeof analyzeFinding>,
    )

    renderWithAuth(
      <Routes>
        <Route path="/scans/:scanId/findings/:findingId" element={<FindingDetailPage />} />
      </Routes>,
      ['/scans/1/findings/3'],
    )

    await screen.findByText('Missing auth')
    await user.click(screen.getByRole('button', { name: /analyze with (ai|gemini)/i }))
    expect(screen.getByRole('button', { name: /ai is analyzing this finding/i })).toBeDisabled()

    resolveAnalyze({
      finding_id: 3,
      ai_analysis: {
        summary: 'Auth is missing on a sensitive route.',
        why_it_matters: 'Unauthorized access risk.',
        technical_reasoning: 'No security requirements found.',
        validation_guidance: 'Confirm in runtime.',
        remediation: 'Require bearer auth.',
        priority: 'HIGH',
        limitations: 'Static analysis only.',
      },
      model: 'gemini-2.5-flash',
      cached: false,
      analyzed_at: '2026-09-14T10:00:00Z',
    })

    mockedGetFinding.mockResolvedValue({
      ...finding,
      ai_analysis: {
        summary: 'Auth is missing on a sensitive route.',
        why_it_matters: 'Unauthorized access risk.',
        technical_reasoning: 'No security requirements found.',
        validation_guidance: 'Confirm in runtime.',
        remediation: 'Require bearer auth.',
        priority: 'HIGH',
        limitations: 'Static analysis only.',
        model: 'gemini-2.5-flash',
        analyzed_at: '2026-09-14T10:00:00Z',
      },
    })

    await waitFor(() => {
      expect(screen.getByText('Auth is missing on a sensitive route.')).toBeInTheDocument()
      expect(screen.getByText(/AI analysis available/i)).toBeInTheDocument()
    })
  })
})

describe('API error handling', () => {
  it('maps 503 to AI unavailable messaging', () => {
    const error = new AxiosError('fail')
    error.response = {
      status: 503,
      data: { detail: 'Gemini unavailable' },
      statusText: 'Service Unavailable',
      headers: {},
      config: { headers: {} as never },
    }
    expect(isAiUnavailable(error)).toBe(true)
    expect(getErrorMessage(error)).toContain('Gemini unavailable')
  })

  it('maps 401 to session expired messaging', () => {
    const error = new AxiosError('unauthorized')
    error.response = {
      status: 401,
      data: { detail: 'Not authenticated' },
      statusText: 'Unauthorized',
      headers: {},
      config: { headers: {} as never },
    }
    expect(getErrorMessage(error)).toMatch(/session has expired/i)
  })
})
