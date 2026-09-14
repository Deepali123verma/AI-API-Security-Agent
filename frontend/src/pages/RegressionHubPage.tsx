import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { GitCompareArrows } from 'lucide-react'
import { listScans } from '../api/scans'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { PageSkeleton } from '../components/Skeleton'
import { RiskBadge, StatusBadge } from '../components/Badges'
import type { ScanHistoryItem } from '../types'
import { getErrorMessage } from '../utils/errors'
import { formatDateTime, formatRiskScore } from '../utils/format'

export function RegressionHubPage() {
  const navigate = useNavigate()
  const [scans, setScans] = useState<ScanHistoryItem[]>([])
  const [currentId, setCurrentId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const response = await listScans({ page: 1, page_size: 100 })
      setScans(response.items)
      const completed = response.items.find((s) => s.status.toUpperCase() === 'COMPLETED')
      if (completed) {
        setCurrentId(String(completed.id))
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load scans for regression.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  if (loading) {
    return <PageSkeleton cards={2} />
  }

  if (error) {
    return (
      <ErrorState title="Unable to open regression hub" message={error} onRetry={() => void load()} />
    )
  }

  const selected = scans.find((s) => String(s.id) === currentId)

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <div className="inline-flex items-center gap-2 rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-sky-800">
          <GitCompareArrows className="h-3.5 w-3.5" />
          Security regression
        </div>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">
          Regression / Compare
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-slate-600">
          Deterministic fingerprint comparison against a baseline scan. Select the current scan to
          open the comparison workspace.
        </p>
      </div>

      {scans.length === 0 ? (
        <EmptyState
          title="No scans available"
          description="Upload and complete at least two scans to run regression analysis."
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
        <section className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
          <label htmlFor="current-scan" className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Current scan
          </label>
          <div className="mt-2 flex flex-wrap items-end gap-3">
            <select
              id="current-scan"
              value={currentId}
              onChange={(e) => setCurrentId(e.target.value)}
              className="min-w-[240px] flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm focus-ring"
            >
              <option value="">Select scan…</option>
              {scans.map((scan) => (
                <option key={scan.id} value={scan.id}>
                  #{scan.id} · {scan.name} · {scan.status}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={!currentId}
              onClick={() => navigate(`/scans/${currentId}/compare`)}
              className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50 focus-ring"
            >
              Open comparison
            </button>
          </div>

          {selected ? (
            <div className="mt-5 flex flex-wrap items-center gap-3 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
              <StatusBadge value={selected.status} />
              <RiskBadge value={selected.risk_level || 'INFO'} />
              <span className="text-sm text-slate-600">
                Score {formatRiskScore(selected.overall_risk_score)} · {selected.finding_count}{' '}
                findings · {formatDateTime(selected.created_at)}
              </span>
            </div>
          ) : null}
        </section>
      )}

      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { title: 'Detect', copy: 'Fingerprint new, resolved, and persistent findings.' },
          { title: 'Analyze', copy: 'Track risk score deltas without AI overriding scores.' },
          { title: 'Protect', copy: 'Download comparison reports for audit trails.' },
        ].map((item) => (
          <div key={item.title} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-sky-700">
              {item.title}
            </p>
            <p className="mt-2 text-sm text-slate-600">{item.copy}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
