import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, ChevronUp, Sparkles } from 'lucide-react'
import type { Finding } from '../types'
import { MethodBadge, RiskBadge, SeverityBadge } from './Badges'
import { splitEndpoint } from '../utils/endpoint'

interface FindingCardProps {
  finding: Finding
  scanId: number
  expandable?: boolean
  defaultOpen?: boolean
}

export function FindingCard({
  finding,
  scanId,
  expandable = false,
  defaultOpen = false,
}: FindingCardProps) {
  const [open, setOpen] = useState(defaultOpen)
  const { method, path } = splitEndpoint(finding.endpoint)

  return (
    <article className="card-interactive rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge value={finding.severity} />
            <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-600">
              Deterministic scanner result
            </span>
          </div>
          <h3 className="mt-2 text-base font-semibold text-slate-900">{finding.title}</h3>
          <p className="mt-1 text-sm text-slate-600">{finding.category}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {method ? <MethodBadge value={method} /> : null}
            <span className="font-mono text-xs text-slate-700">{path || finding.endpoint || '—'}</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <RiskBadge value={finding.risk_level} />
          <span className="rounded-lg bg-slate-50 px-2.5 py-1 text-xs font-semibold tabular-nums text-slate-800 ring-1 ring-slate-200">
            Risk Score: {finding.risk_score}
          </span>
        </div>
      </div>

      {expandable ? (
        <button
          type="button"
          className="mt-3 inline-flex items-center gap-1 rounded text-sm font-medium text-sky-700 hover:text-sky-600 focus-ring"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
        >
          {open ? (
            <>
              Collapse details <ChevronUp className="h-4 w-4" />
            </>
          ) : (
            <>
              Expand details <ChevronDown className="h-4 w-4" />
            </>
          )}
        </button>
      ) : null}

      {(!expandable || open) ? (
        <div className="mt-4 space-y-3 border-t border-slate-100 pt-4">
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Category</dt>
              <dd className="mt-1 font-medium text-slate-900">{finding.category}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">HTTP Method</dt>
              <dd className="mt-1 font-medium text-slate-900">{method || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Endpoint</dt>
              <dd className="mt-1 font-mono text-xs text-slate-800">{path || finding.endpoint || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Confidence</dt>
              <dd className="mt-1 font-medium text-slate-900">{finding.confidence}</dd>
            </div>
          </dl>

          {finding.risk_factors ? (
            <div className="rounded-xl bg-slate-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Risk factors</p>
              <pre className="mt-1 overflow-x-auto text-xs text-slate-700">
                {JSON.stringify(finding.risk_factors, null, 2)}
              </pre>
            </div>
          ) : null}

          {finding.evidence ? (
            <div className="rounded-xl bg-slate-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Evidence</p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{finding.evidence}</p>
            </div>
          ) : null}

          {finding.ai_analysis ? (
            <div className="rounded-xl border border-violet-200 bg-violet-50/60 p-3">
              <p className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-violet-800">
                <Sparkles className="h-3.5 w-3.5" />
                AI reasoning available
              </p>
              <p className="mt-1 line-clamp-2 text-sm text-slate-700">{finding.ai_analysis.summary}</p>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="mt-4 flex justify-end">
        <Link
          to={`/scans/${scanId}/findings/${finding.id}`}
          className="rounded-xl bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800 focus-ring"
        >
          View details
        </Link>
      </div>
    </article>
  )
}
