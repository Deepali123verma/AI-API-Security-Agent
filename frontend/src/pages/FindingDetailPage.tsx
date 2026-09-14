import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { analyzeFinding, getFindingById } from '../api/scans'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { RiskBadge, SeverityBadge } from '../components/Badges'
import type { Finding } from '../types'
import { getErrorMessage, getErrorStatus, isAiUnavailable } from '../utils/errors'
import { formatDateTime } from '../utils/format'

export function FindingDetailPage() {
  const { scanId, findingId } = useParams()
  const scanNumericId = Number(scanId)
  const findingNumericId = Number(findingId)

  const [finding, setFinding] = useState<Finding | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [errorStatus, setErrorStatus] = useState<number | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)
  const [aiNotice, setAiNotice] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!Number.isFinite(scanNumericId) || !Number.isFinite(findingNumericId)) {
      setError('Invalid finding id.')
      setErrorStatus(400)
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await getFindingById(scanNumericId, findingNumericId)
      if (!data) {
        setFinding(null)
        setError('Finding not found.')
        setErrorStatus(404)
      } else {
        setFinding(data)
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load finding.'))
      setErrorStatus(getErrorStatus(err))
      setFinding(null)
    } finally {
      setLoading(false)
    }
  }, [scanNumericId, findingNumericId])

  useEffect(() => {
    void load()
  }, [load])

  async function runAnalysis(forceRefresh: boolean) {
    setAnalyzing(true)
    setAiError(null)
    setAiNotice(null)
    try {
      const result = await analyzeFinding(scanNumericId, findingNumericId, forceRefresh)
      setFinding((current) =>
        current
          ? {
              ...current,
              ai_analysis: {
                ...result.ai_analysis,
                model: result.model,
                analyzed_at: result.analyzed_at,
              },
            }
          : current,
      )
      setAiNotice(
        result.cached
          ? 'Showing cached AI analysis.'
          : forceRefresh
            ? 'AI analysis refreshed.'
            : 'AI analysis completed.',
      )
      await load()
    } catch (err) {
      if (isAiUnavailable(err)) {
        setAiError(
          'AI analysis is temporarily unavailable. The deterministic security finding is still available.',
        )
      } else {
        setAiError(getErrorMessage(err, 'AI analysis failed.'))
      }
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) {
    return <LoadingState label="Loading finding…" />
  }

  if (error || !finding) {
    return (
      <ErrorState
        title={errorStatus === 404 ? 'Finding not found' : 'Unable to load finding'}
        message={error || 'Finding not found.'}
        onRetry={() => void load()}
      />
    )
  }

  const hasAi = Boolean(finding.ai_analysis?.summary)

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <p className="text-sm text-slate-500">
          <Link to={`/scans/${scanNumericId}/findings`} className="text-sky-700 hover:underline">
            Findings
          </Link>{' '}
          / #{finding.id}
        </p>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
          <h1 className="text-2xl font-semibold text-slate-900">{finding.title}</h1>
          <div className="flex flex-wrap gap-2">
            <SeverityBadge value={finding.severity} />
            <RiskBadge value={finding.risk_level} />
          </div>
        </div>
      </div>

      <section className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-500">
            Deterministic Scanner Result
          </h2>
          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-600">
            Authoritative
          </span>
        </div>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-slate-500">Category</dt>
            <dd className="font-medium text-slate-900">{finding.category}</dd>
          </div>
          <div>
            <dt className="text-slate-500">OWASP</dt>
            <dd className="font-medium text-slate-900">{finding.owasp_category || '—'}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Risk score</dt>
            <dd className="font-medium tabular-nums text-slate-900">{finding.risk_score}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Confidence</dt>
            <dd className="font-medium text-slate-900">{finding.confidence}</dd>
          </div>
        </dl>
        {finding.description ? (
          <p className="mt-4 text-sm text-slate-700">{finding.description}</p>
        ) : null}
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Evidence</h2>
        <pre className="mt-3 overflow-x-auto whitespace-pre-wrap rounded-md bg-slate-50 p-4 text-sm text-slate-800">
          {finding.evidence}
        </pre>
        {finding.structured_evidence ? (
          <pre className="mt-3 overflow-x-auto rounded-md bg-slate-950 p-4 text-xs text-slate-100">
            {JSON.stringify(finding.structured_evidence, null, 2)}
          </pre>
        ) : null}
      </section>

      {finding.risk_factors ? (
        <section className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Risk factors
          </h2>
          <pre className="mt-3 overflow-x-auto rounded-md bg-slate-50 p-4 text-xs text-slate-800">
            {JSON.stringify(finding.risk_factors, null, 2)}
          </pre>
        </section>
      ) : null}

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Endpoint</h2>
        <p className="mt-3 font-mono text-sm text-slate-900">{finding.endpoint || '—'}</p>
        <p className="mt-2 text-sm text-slate-600">
          Deterministic remediation: {finding.remediation}
        </p>
      </section>

      <section className="rounded-2xl border border-violet-200 bg-gradient-to-br from-violet-50 via-white to-sky-50 p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.14em] text-violet-800">
            <Sparkles className="h-4 w-4" aria-hidden />
            AI Reasoning
          </h2>
          <div className="flex flex-wrap gap-2">
            {hasAi ? (
              <>
                <span className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-800 ring-1 ring-emerald-200">
                  AI analysis available
                </span>
                <button
                  type="button"
                  disabled={analyzing}
                  onClick={() => void runAnalysis(true)}
                  className="rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-60 focus-ring"
                >
                  {analyzing ? 'AI is analyzing this finding…' : 'Refresh analysis'}
              </button>
              </>
            ) : (
              <button
                type="button"
                disabled={analyzing}
                onClick={() => void runAnalysis(false)}
                className="inline-flex items-center gap-2 rounded-xl bg-violet-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-violet-600 disabled:opacity-60 focus-ring"
              >
                <Sparkles className="h-4 w-4" aria-hidden />
                {analyzing ? 'AI is analyzing this finding…' : 'Analyze with Gemini'}
              </button>
            )}
          </div>
        </div>

        {analyzing ? (
          <p className="mt-3 rounded-xl border border-violet-200 bg-white/80 px-3 py-2 text-sm text-violet-900" role="status">
            AI is analyzing this finding… Deterministic evidence remains authoritative.
          </p>
        ) : null}

        {aiNotice ? (
          <p className="mt-3 text-sm text-emerald-700">{aiNotice}</p>
        ) : null}
        {aiError ? (
          <p className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900" role="alert">
            {aiError}
          </p>
        ) : null}

        <p className="mt-3 text-xs text-slate-500">
          Gemini provides contextual reasoning only. It does not override risk score, severity, or
          evidence.
        </p>

        {hasAi && finding.ai_analysis ? (
          <div className="mt-4 grid gap-4">
            {(
              [
                ['Summary', finding.ai_analysis.summary],
                ['Why it matters', finding.ai_analysis.why_it_matters],
                ['Technical reasoning', finding.ai_analysis.technical_reasoning],
                ['Validation guidance', finding.ai_analysis.validation_guidance],
                ['Remediation', finding.ai_analysis.remediation],
                ['Priority', finding.ai_analysis.priority],
                ['Limitations', finding.ai_analysis.limitations],
              ] as const
            ).map(([label, value]) =>
              value ? (
                <div key={label} className="rounded-xl border border-violet-100 bg-white p-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {label}
                  </h3>
                  <p className="mt-2 whitespace-pre-wrap text-sm text-slate-800">{value}</p>
                </div>
              ) : null,
            )}
            <p className="text-xs text-slate-500">
              Model: {finding.ai_analysis.model || '—'} · Analyzed:{' '}
              {formatDateTime(finding.ai_analysis.analyzed_at)}
            </p>
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-600">
            AI analysis hasn’t been run yet. Deterministic evidence and risk scoring remain
            authoritative.
          </p>
        )}
      </section>
    </div>
  )
}
