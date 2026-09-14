import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import {
  downloadScanReportPdf,
  getScan,
  listFindings,
  runSecurityScan,
} from '../api/scans'
import { ErrorState } from '../components/ErrorState'
import { EmptyState } from '../components/EmptyState'
import { FindingCard } from '../components/FindingCard'
import { PageSkeleton } from '../components/Skeleton'
import { RiskGauge, SeverityDistribution } from '../components/RiskVisuals'
import { RiskBadge, StatusBadge } from '../components/Badges'
import { CompareScanLink } from '../components/RegressionSections'
import { StatCard } from '../components/StatCard'
import { Tooltip } from '../components/Tooltip'
import { useToast } from '../context/ToastContext'
import type { Finding, ScanDetail } from '../types'
import { getErrorMessage, getErrorStatus } from '../utils/errors'
import { formatDateTime } from '../utils/format'
import { SEVERITY_ORDER } from '../utils/badges'

export function ScanDetailPage() {
  const { scanId } = useParams()
  const id = Number(scanId)
  const toast = useToast()
  const [scan, setScan] = useState<ScanDetail | null>(null)
  const [findings, setFindings] = useState<Finding[]>([])
  const [severityFilter, setSeverityFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [findingsLoading, setFindingsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorStatus, setErrorStatus] = useState<number | null>(null)
  const [scanning, setScanning] = useState(false)
  const [downloadingReport, setDownloadingReport] = useState(false)

  const load = useCallback(async () => {
    if (!Number.isFinite(id)) {
      setError('Invalid scan id.')
      setErrorStatus(400)
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    setErrorStatus(null)
    try {
      const data = await getScan(id)
      setScan(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load scan detail.'))
      setErrorStatus(getErrorStatus(err))
      setScan(null)
    } finally {
      setLoading(false)
    }
  }, [id])

  const loadFindings = useCallback(async () => {
    if (!Number.isFinite(id)) {
      return
    }
    setFindingsLoading(true)
    try {
      const response = await listFindings(id, {
        page: 1,
        page_size: 100,
        severity: severityFilter || undefined,
      })
      setFindings(response.items)
    } catch {
      setFindings([])
    } finally {
      setFindingsLoading(false)
    }
  }, [id, severityFilter])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    void loadFindings()
  }, [loadFindings])

  const severityCounts = useMemo(
    () => ({
      CRITICAL: scan?.summary.critical || 0,
      HIGH: scan?.summary.high || 0,
      MEDIUM: scan?.summary.medium || 0,
      LOW: scan?.summary.low || 0,
      INFO: scan?.summary.info || 0,
    }),
    [scan],
  )

  async function handleSecurityScan() {
    setScanning(true)
    try {
      const result = await runSecurityScan(id)
      toast.success(
        `Security scan completed: ${result.total_findings} findings (${result.risk_level}, score ${result.overall_risk_score}).`,
      )
      await load()
      await loadFindings()
    } catch (err) {
      toast.error(getErrorMessage(err, 'Security scan failed.'))
    } finally {
      setScanning(false)
    }
  }

  async function handleDownloadReport() {
    setDownloadingReport(true)
    try {
      await downloadScanReportPdf(id)
      toast.success('Security report download started.')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Unable to download security report.'))
    } finally {
      setDownloadingReport(false)
    }
  }

  if (loading) {
    return <PageSkeleton cards={3} />
  }

  if (error || !scan) {
    return (
      <ErrorState
        title={errorStatus === 404 ? 'Scan not found' : 'Unable to load scan'}
        message={error || 'Scan not found.'}
        onRetry={() => void load()}
      />
    )
  }

  const canRunScan = ['PENDING', 'COMPLETED', 'FAILED'].includes(scan.status.toUpperCase())

  return (
    <div className="space-y-6 animate-fade-up">
      <div className="rounded-3xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm text-slate-500">
              <Link to="/scans" className="text-sky-700 hover:underline">
                Scans
              </Link>{' '}
              / #{scan.id}
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{scan.name}</h1>
            <p className="mt-1 text-sm text-slate-600">{scan.source_filename}</p>
            <p className="mt-2 text-xs text-slate-500">Created {formatDateTime(scan.created_at)}</p>
          </div>
          <StatusBadge value={scan.status} />
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          {canRunScan ? (
            <button
              type="button"
              disabled={scanning}
              onClick={() => void handleSecurityScan()}
              className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60 focus-ring"
            >
              {scanning ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {scanning ? 'Running scan…' : 'Run security scan'}
            </button>
          ) : null}
          <button
            type="button"
            disabled={downloadingReport}
            onClick={() => void handleDownloadReport()}
            className="rounded-xl bg-sky-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-sky-600 disabled:opacity-60 focus-ring"
          >
            {downloadingReport ? 'Preparing report…' : 'Download security report'}
          </button>
          <CompareScanLink scanId={scan.id} />
          <Link
            to={`/scans/${scan.id}/endpoints`}
            className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-800 hover:bg-slate-50 focus-ring"
          >
            View endpoints
          </Link>
          <Link
            to={`/scans/${scan.id}/findings`}
            className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-800 hover:bg-slate-50 focus-ring"
          >
            View all findings
          </Link>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
        <RiskGauge
          score={scan.summary.overall_risk_score}
          level={scan.summary.risk_level}
          metrics={[
            { label: 'Endpoints', value: scan.summary.endpoint_count, to: `/scans/${scan.id}/endpoints` },
            { label: 'Findings', value: scan.summary.finding_count, to: `/scans/${scan.id}/findings` },
            { label: 'AI Analyzed', value: scan.summary.ai_analysis_count },
          ]}
        />
        <SeverityDistribution counts={severityCounts} viewAllTo={`/scans/${scan.id}/findings`} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Risk Score" value={scan.summary.overall_risk_score} />
        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Risk Level</p>
          <div className="mt-3">
            <RiskBadge value={scan.summary.risk_level} />
          </div>
        </div>
        <StatCard label="Endpoints" value={scan.summary.endpoint_count} to={`/scans/${scan.id}/endpoints`} />
        <StatCard label="Findings" value={scan.summary.finding_count} to={`/scans/${scan.id}/findings`} />
      </div>

      <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-500">
          Scan information
        </h2>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Created</dt>
            <dd className="text-slate-900">{formatDateTime(scan.created_at)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Completed</dt>
            <dd className="text-slate-900">{formatDateTime(scan.completed_at)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Spec title</dt>
            <dd className="text-right text-slate-900">{scan.title || '—'}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">OpenAPI version</dt>
            <dd className="text-slate-900">{scan.specification_version || '—'}</dd>
          </div>
        </dl>
      </div>

      <section className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Security Findings</h2>
            <p className="text-sm text-slate-600">
              Expand cards for deterministic evidence. Open a finding for Gemini AI reasoning.
            </p>
          </div>
          <div>
            <label htmlFor="detail-severity" className="mb-1 block text-xs font-medium uppercase text-slate-500">
              Severity filter
            </label>
            <select
              id="detail-severity"
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus-ring"
            >
              <option value="">All</option>
              {SEVERITY_ORDER.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </div>
        </div>

        {findingsLoading ? <TableishLoader /> : null}
        {!findingsLoading && findings.length === 0 ? (
          <EmptyState
            title="No security findings detected"
            description="Run a security scan or clear the severity filter."
          />
        ) : null}
        {!findingsLoading && findings.length > 0 ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {findings.slice(0, 8).map((finding) => (
              <FindingCard key={finding.id} finding={finding} scanId={id} expandable />
            ))}
          </div>
        ) : null}
        {!findingsLoading && findings.length > 8 ? (
          <Tooltip content="Open the full paginated findings view">
            <Link to={`/scans/${id}/findings`} className="text-sm font-medium text-sky-700 hover:underline">
              View remaining findings →
            </Link>
          </Tooltip>
        ) : null}
      </section>
    </div>
  )
}

function TableishLoader() {
  return (
    <div className="grid gap-4 lg:grid-cols-2" role="status" aria-label="Loading findings">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="h-40 rounded-2xl border border-slate-200 bg-white p-4">
          <div className="skeleton h-4 w-2/3" />
          <div className="skeleton mt-3 h-3 w-1/2" />
          <div className="skeleton mt-6 h-16 w-full" />
        </div>
      ))}
    </div>
  )
}
