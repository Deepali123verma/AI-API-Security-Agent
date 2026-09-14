import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  CheckCircle2,
  FileSearch,
  ShieldAlert,
  Sparkles,
  ArrowRight,
} from 'lucide-react'
import { getScan, listFindings, listScans } from '../api/scans'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { ScanTable } from '../components/ScanTable'
import { PageSkeleton } from '../components/Skeleton'
import { StatCard } from '../components/StatCard'
import { RiskGauge, SeverityDistribution } from '../components/RiskVisuals'
import { MethodBadge, SeverityBadge } from '../components/Badges'
import { useAuth } from '../context/AuthContext'
import type { Finding, ScanDetail, ScanHistoryItem } from '../types'
import { getErrorMessage } from '../utils/errors'
import { SEVERITY_ORDER } from '../utils/badges'
import { splitEndpoint } from '../utils/endpoint'
import { formatDateTime } from '../utils/format'

export function DashboardPage() {
  const { user } = useAuth()
  const [scans, setScans] = useState<ScanHistoryItem[]>([])
  const [total, setTotal] = useState(0)
  const [focusScan, setFocusScan] = useState<ScanDetail | null>(null)
  const [latestFindings, setLatestFindings] = useState<Finding[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const response = await listScans({ page: 1, page_size: 100 })
      setScans(response.items)
      setTotal(response.total)

      const completed = response.items.find((s) => s.status.toUpperCase() === 'COMPLETED')
      if (completed) {
        const [detail, findings] = await Promise.all([
          getScan(completed.id),
          listFindings(completed.id, { page: 1, page_size: 8 }),
        ])
        setFocusScan(detail)
        setLatestFindings(findings.items)
      } else {
        setFocusScan(null)
        setLatestFindings([])
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load dashboard data.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const stats = useMemo(() => {
    const completed = scans.filter((s) => s.status.toUpperCase() === 'COMPLETED').length
    const findings = scans.reduce((sum, s) => sum + (s.finding_count || 0), 0)
    const highCriticalFindings = focusScan
      ? (focusScan.summary.critical || 0) + (focusScan.summary.high || 0)
      : scans.filter((s) => {
          const level = (s.risk_level || '').toUpperCase()
          return level === 'HIGH' || level === 'CRITICAL'
        }).length

    return { completed, findings, highCriticalFindings }
  }, [scans, focusScan])

  const severityCounts = useMemo(
    () => ({
      CRITICAL: focusScan?.summary.critical || 0,
      HIGH: focusScan?.summary.high || 0,
      MEDIUM: focusScan?.summary.medium || 0,
      LOW: focusScan?.summary.low || 0,
      INFO: focusScan?.summary.info || 0,
    }),
    [focusScan],
  )

  const filteredScans = useMemo(() => scans.slice(0, 8), [scans])

  if (loading) {
    return <PageSkeleton />
  }

  if (error) {
    return <ErrorState title="Unable to load dashboard" message={error} onRetry={() => void load()} />
  }

  const focusId = focusScan?.id
  const findingsLink = focusId ? `/scans/${focusId}/findings` : '/findings'
  const analyzed = focusScan?.summary.ai_analysis_count ?? 0
  const unanalyzed = Math.max(0, (focusScan?.summary.finding_count || 0) - analyzed)

  return (
    <div className="space-y-6 animate-fade-up">
      <section className="hero-grid relative overflow-hidden rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm sm:p-8">
        <div className="relative z-10 max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-700">
            Security command center
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
            Welcome back, {user?.username || 'analyst'}
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-slate-600 sm:text-base">
            Monitor and secure your APIs with AI-powered threat detection and intelligent analysis.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              to="/scans"
              className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 focus-ring"
            >
              New scan <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/regression"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white/80 px-4 py-2.5 text-sm font-medium text-slate-800 hover:bg-white focus-ring"
            >
              Run regression
            </Link>
          </div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total Scans"
          value={total}
          to="/scans"
          hint="OpenAPI files scanned"
          icon={<FileSearch className="h-4 w-4" />}
        />
        <StatCard
          label="Completed Scans"
          value={stats.completed}
          to="/scans?status=COMPLETED"
          hint="Successfully completed"
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-600" />}
        />
        <StatCard
          label="Total Findings"
          value={stats.findings}
          to={findingsLink}
          hint="Across all scans"
          icon={<ShieldAlert className="h-4 w-4 text-sky-700" />}
        />
        <StatCard
          label="High / Critical"
          value={stats.highCriticalFindings}
          to={focusId ? `${findingsLink}?severity=` : '/findings'}
          hint={focusScan ? 'High or critical severity' : 'Scans with high/critical risk'}
          icon={<AlertTriangle className="h-4 w-4 text-orange-600" />}
          accent="border-orange-200"
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {focusScan ? (
          <RiskGauge
            score={focusScan.summary.overall_risk_score}
            level={focusScan.summary.risk_level}
            metrics={[
              {
                label: 'Endpoints',
                value: focusScan.summary.endpoint_count,
                to: `/scans/${focusScan.id}/endpoints`,
              },
              {
                label: 'Findings',
                value: focusScan.summary.finding_count,
                to: `/scans/${focusScan.id}/findings`,
              },
              { label: 'AI Analyzed', value: focusScan.summary.ai_analysis_count },
            ]}
            reportTo={`/scans/${focusScan.id}`}
          />
        ) : (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-500">
              Overall Security Posture
            </h2>
            <EmptyState
              title="No completed scans yet"
              description="Upload an OpenAPI specification and run a security scan to populate posture metrics."
              action={
                <Link
                  to="/scans"
                  className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white focus-ring"
                >
                  Upload OpenAPI Specification
                </Link>
              }
            />
          </div>
        )}

        <SeverityDistribution
          counts={severityCounts}
          viewAllTo={findingsLink}
        />
      </div>

      <section className="overflow-hidden rounded-2xl border border-violet-200/80 bg-gradient-to-br from-violet-50 via-white to-sky-50 p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-violet-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-violet-800">
              <Sparkles className="h-3.5 w-3.5" />
              AI Analysis
            </div>
            <h2 className="mt-3 text-xl font-semibold text-slate-900">Gemini reasoning layer</h2>
            <p className="mt-2 text-sm text-slate-600">
              Get intelligent insights and recommendations for your findings. Deterministic scanners
              stay authoritative — Gemini never overrides risk scores.
            </p>
          </div>
          <div className="rounded-2xl border border-violet-200 bg-white/80 px-5 py-4 text-center">
            <p className="text-xs uppercase tracking-wide text-violet-700">Analyzed findings</p>
            <p className="mt-1 text-3xl font-semibold tabular-nums text-slate-900">{analyzed}</p>
            <p className="mt-1 text-xs text-slate-500">
              {focusScan ? `${unanalyzed} awaiting analysis` : 'N/A'}
            </p>
          </div>
        </div>
        <div className="mt-5">
          {focusScan ? (
            <Link
              to={`/scans/${focusScan.id}/findings`}
              className="inline-flex items-center gap-2 rounded-xl bg-violet-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-violet-600 focus-ring"
            >
              Open findings for AI analysis <ArrowRight className="h-4 w-4" />
            </Link>
          ) : (
            <p className="text-sm text-slate-600">AI analysis hasn’t been run yet.</p>
          )}
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Recent Scans</h2>
            <p className="text-sm text-slate-600">Live scan history from FastAPI — no simulated rows.</p>
          </div>
          <Link to="/scans" className="text-sm font-medium text-sky-700 hover:text-sky-600">
            View all →
          </Link>
        </div>
        {scans.length === 0 ? (
          <EmptyState
            title="No scans yet."
            description="Upload an OpenAPI specification to start your first security scan."
            action={
              <Link
                to="/scans"
                className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white focus-ring"
              >
                Upload OpenAPI Specification
              </Link>
            }
          />
        ) : (
          <ScanTable scans={filteredScans} />
        )}
        {total > scans.length ? (
          <p className="mt-2 text-xs text-slate-500">
            Showing latest {scans.length} of {total} scans returned by the API.
          </p>
        ) : null}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Latest Findings</h2>
            <p className="text-sm text-slate-600">
              {focusScan
                ? `From ${focusScan.name} · updated ${formatDateTime(focusScan.updated_at || focusScan.created_at)}`
                : 'Complete a scan to populate findings.'}
            </p>
          </div>
          <Link to={findingsLink} className="text-sm font-medium text-sky-700 hover:text-sky-600">
            View all →
          </Link>
        </div>

        {!focusScan || latestFindings.length === 0 ? (
          <EmptyState
            title="No security findings detected"
            description={
              focusScan
                ? 'This completed scan has no findings yet — or security scan has not been run.'
                : 'Run a security scan after uploading an OpenAPI specification.'
            }
          />
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-sm">
            <ul className="divide-y divide-slate-100">
              {latestFindings.map((finding) => {
                const { method, path } = splitEndpoint(finding.endpoint)
                return (
                  <li key={finding.id}>
                    <Link
                      to={`/scans/${focusScan.id}/findings/${finding.id}`}
                      className="flex flex-wrap items-center gap-3 px-4 py-3.5 transition hover:bg-slate-50 focus-ring"
                    >
                      <SeverityBadge value={finding.severity} />
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium text-slate-900">{finding.title}</p>
                        <p className="mt-0.5 text-xs text-slate-500">{finding.category}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        {method ? <MethodBadge value={method} /> : null}
                        <span className="max-w-[12rem] truncate font-mono text-xs text-slate-600">
                          {path || finding.endpoint || '—'}
                        </span>
                      </div>
                      <span className="tabular-nums text-sm font-semibold text-slate-800">
                        {finding.risk_score}
                      </span>
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        )}
      </section>

      <p className="text-xs text-slate-500">
        Severity keys tracked: {SEVERITY_ORDER.join(' · ')}. Posture metrics use the most recent
        completed scan when available.
      </p>
    </div>
  )
}
