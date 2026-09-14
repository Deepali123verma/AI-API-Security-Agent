import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import {
  compareScans,
  downloadComparisonReportPdf,
  listScans,
} from '../api/scans'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import {
  CompareMetricCard,
  PostureBanner,
  RegressionFindingList,
} from '../components/RegressionSections'
import { PageSkeleton } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'
import type { RegressionResponse, ScanHistoryItem } from '../types'
import { getErrorMessage, getErrorStatus } from '../utils/errors'

export function ComparePage() {
  const { scanId, baselineScanId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const currentId = Number(scanId)
  const baselineId = baselineScanId ? Number(baselineScanId) : null

  const [candidates, setCandidates] = useState<ScanHistoryItem[]>([])
  const [selectedBaseline, setSelectedBaseline] = useState<string>(
    baselineId && Number.isFinite(baselineId) ? String(baselineId) : '',
  )
  const [comparison, setComparison] = useState<RegressionResponse | null>(null)
  const [loadingList, setLoadingList] = useState(true)
  const [loadingCompare, setLoadingCompare] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorStatus, setErrorStatus] = useState<number | null>(null)

  const loadCandidates = useCallback(async () => {
    if (!Number.isFinite(currentId)) {
      setError('Invalid scan id.')
      setLoadingList(false)
      return
    }
    setLoadingList(true)
    setError(null)
    try {
      const response = await listScans({ page: 1, page_size: 100 })
      setCandidates(response.items.filter((item) => item.id !== currentId))
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load comparison candidates.'))
      setErrorStatus(getErrorStatus(err))
    } finally {
      setLoadingList(false)
    }
  }, [currentId])

  const loadComparison = useCallback(
    async (baseline: number) => {
      setLoadingCompare(true)
      setError(null)
      setErrorStatus(null)
      try {
        const data = await compareScans(currentId, baseline)
        setComparison(data)
      } catch (err) {
        setComparison(null)
        setError(getErrorMessage(err, 'Unable to compare scans.'))
        setErrorStatus(getErrorStatus(err))
      } finally {
        setLoadingCompare(false)
      }
    },
    [currentId],
  )

  useEffect(() => {
    void loadCandidates()
  }, [loadCandidates])

  useEffect(() => {
    if (baselineId && Number.isFinite(baselineId)) {
      setSelectedBaseline(String(baselineId))
      void loadComparison(baselineId)
    } else {
      setComparison(null)
    }
  }, [baselineId, loadComparison])

  const completedCandidates = useMemo(
    () => candidates.filter((item) => item.status.toUpperCase() === 'COMPLETED'),
    [candidates],
  )
  const otherCandidates = useMemo(
    () => candidates.filter((item) => item.status.toUpperCase() !== 'COMPLETED'),
    [candidates],
  )

  function handleSelectBaseline() {
    const value = Number(selectedBaseline)
    if (!Number.isFinite(value) || value === currentId) {
      setError('Select a different scan as the baseline.')
      return
    }
    navigate(`/scans/${currentId}/compare/${value}`)
  }

  async function handleDownloadComparison() {
    if (!baselineId) {
      return
    }
    setDownloading(true)
    setError(null)
    try {
      await downloadComparisonReportPdf(currentId, baselineId)
      toast.success('Comparison report download started.')
    } catch (err) {
      const message = getErrorMessage(err, 'Unable to download comparison report.')
      setError(message)
      toast.error(message)
    } finally {
      setDownloading(false)
    }
  }

  if (loadingList) {
    return <PageSkeleton cards={3} />
  }

  const changePositive =
    comparison == null
      ? null
      : comparison.risk_score_change < 0
        ? true
        : comparison.risk_score_change > 0
          ? false
          : null

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <p className="text-sm text-slate-500">
          <Link to={`/scans/${currentId}`} className="text-sky-700 hover:underline">
            Scan #{currentId}
          </Link>{' '}
          / Compare
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">Security Regression</h1>
        <p className="mt-1 text-sm text-slate-600">
          Deterministic fingerprint comparison against a baseline scan.
        </p>
      </div>

      <section className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-500">
          Select baseline scan
        </h2>
        {candidates.length === 0 ? (
          <EmptyState
            title="No other scans available"
            description="Upload and scan another specification to enable regression comparison."
          />
        ) : (
          <div className="mt-4 flex flex-wrap items-end gap-3">
            <div className="min-w-[240px] flex-1">
              <label htmlFor="baseline" className="mb-1 block text-sm font-medium text-slate-700">
                Baseline
              </label>
              <select
                id="baseline"
                value={selectedBaseline}
                onChange={(e) => setSelectedBaseline(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm focus-ring"
              >
                <option value="">Choose a previous scan…</option>
                {completedCandidates.length > 0 ? (
                  <optgroup label="Completed scans">
                    {completedCandidates.map((item) => (
                      <option key={item.id} value={item.id}>
                        #{item.id} · {item.name} · {item.risk_level || 'N/A'} (
                        {item.overall_risk_score ?? '—'})
                      </option>
                    ))}
                  </optgroup>
                ) : null}
                {otherCandidates.length > 0 ? (
                  <optgroup label="Other scans">
                    {otherCandidates.map((item) => (
                      <option key={item.id} value={item.id}>
                        #{item.id} · {item.name} · {item.status}
                      </option>
                    ))}
                  </optgroup>
                ) : null}
              </select>
            </div>
            <button
              type="button"
              onClick={handleSelectBaseline}
              disabled={!selectedBaseline || loadingCompare}
              className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50 focus-ring"
            >
              {loadingCompare ? 'Comparing…' : 'Run comparison'}
            </button>
          </div>
        )}
      </section>

      {error ? (
        <ErrorState
          title={errorStatus === 404 ? 'Scan not found' : 'Comparison error'}
          message={error}
          onRetry={
            baselineId
              ? () => void loadComparison(baselineId)
              : () => void loadCandidates()
          }
        />
      ) : null}

      {loadingCompare ? <LoadingState label="Comparing scans…" /> : null}

      {!loadingCompare && comparison ? (
        <div className="space-y-5">
          <PostureBanner posture={comparison.posture} summary={comparison.summary} />

          <div className="grid gap-4 md:grid-cols-3">
            <CompareMetricCard
              label="Baseline risk"
              value={comparison.baseline_risk_score}
              badge={comparison.baseline_risk_level}
              subtitle={`#${comparison.baseline_scan.id} · ${comparison.baseline_scan.name}`}
            />
            <CompareMetricCard
              label="Current risk"
              value={comparison.current_risk_score}
              badge={comparison.current_risk_level}
              subtitle={`#${comparison.current_scan.id} · ${comparison.current_scan.name}`}
            />
            <div className="card-interactive rounded-lg border border-slate-200 bg-white p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Risk score change
              </p>
              <div className="mt-2 flex items-center gap-2">
                {comparison.risk_score_change < 0 ? (
                  <ArrowDownRight className="h-5 w-5 text-emerald-600" />
                ) : comparison.risk_score_change > 0 ? (
                  <ArrowUpRight className="h-5 w-5 text-rose-600" />
                ) : (
                  <Minus className="h-5 w-5 text-slate-500" />
                )}
                <p
                  className={`text-3xl font-semibold tabular-nums ${
                    changePositive === true
                      ? 'text-emerald-700'
                      : changePositive === false
                        ? 'text-rose-700'
                        : 'text-slate-900'
                  }`}
                >
                  {comparison.risk_score_change > 0 ? '+' : ''}
                  {comparison.risk_score_change}
                </p>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                New critical: {comparison.new_critical_count} · Resolved critical:{' '}
                {comparison.resolved_critical_count}
              </p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <CompareMetricCard
              label="New findings"
              value={comparison.new_findings.length}
              positive={false}
              subtitle="Introduced since baseline"
            />
            <CompareMetricCard
              label="Resolved findings"
              value={comparison.resolved_findings.length}
              positive
              subtitle="Present in baseline only"
            />
            <CompareMetricCard
              label="Persistent findings"
              value={comparison.persistent_findings.length}
              subtitle="Still open in both scans"
            />
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              disabled={downloading}
              onClick={() => void handleDownloadComparison()}
              className="rounded-md bg-sky-700 px-4 py-2 text-sm font-medium text-white hover:bg-sky-600 disabled:opacity-60 focus-ring"
            >
              {downloading ? 'Downloading…' : 'Download comparison report'}
            </button>
          </div>

          <RegressionFindingList
            title="New findings"
            description="Present in the current scan but not the baseline."
            kind="new"
            findings={comparison.new_findings}
            emptyLabel="No new findings."
          />
          <RegressionFindingList
            title="Resolved findings"
            description="Present in the baseline but not the current scan."
            kind="resolved"
            findings={comparison.resolved_findings}
            emptyLabel="No resolved findings."
          />
          <RegressionFindingList
            title="Persistent findings"
            description="Present in both scans."
            kind="persistent"
            findings={comparison.persistent_findings}
            emptyLabel="No persistent findings."
          />
        </div>
      ) : null}
    </div>
  )
}
