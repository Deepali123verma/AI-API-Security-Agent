import { Link } from 'react-router-dom'
import type { RegressionFindingItem } from '../types'
import { MethodBadge, RiskBadge, SeverityBadge } from './Badges'
import { AnimatedNumber } from './AnimatedNumber'

type ChangeKind = 'new' | 'resolved' | 'persistent'

const KIND_STYLES: Record<ChangeKind, string> = {
  new: 'border-rose-200 bg-rose-50/70',
  resolved: 'border-emerald-200 bg-emerald-50/70',
  persistent: 'border-slate-200 bg-white',
}

const KIND_LABELS: Record<ChangeKind, string> = {
  new: 'NEW',
  resolved: 'RESOLVED',
  persistent: 'PERSISTENT',
}

interface RegressionFindingListProps {
  title: string
  description?: string
  kind: ChangeKind
  findings: RegressionFindingItem[]
  emptyLabel: string
}

export function RegressionFindingList({
  title,
  description,
  kind,
  findings,
  emptyLabel,
}: RegressionFindingListProps) {
  return (
    <section className={`rounded-lg border p-5 animate-fade-up ${KIND_STYLES[kind]}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          {description ? <p className="mt-1 text-sm text-slate-600">{description}</p> : null}
        </div>
        <span className="rounded-md bg-white/90 px-2 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700 ring-1 ring-slate-200">
          {KIND_LABELS[kind]} · {findings.length}
        </span>
      </div>

      {findings.length === 0 ? (
        <p className="mt-4 text-sm text-slate-600">{emptyLabel}</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {findings.map((finding) => (
            <li
              key={`${kind}-${finding.id}-${finding.fingerprint}`}
              className="card-interactive rounded-md border border-slate-200/80 bg-white px-4 py-3"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-medium text-slate-900">{finding.title}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    {finding.method ? <MethodBadge value={finding.method} /> : null}
                    <span className="font-mono text-xs text-slate-600">
                      {finding.path || finding.endpoint || '—'}
                    </span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <SeverityBadge value={finding.severity} />
                  <RiskBadge value={finding.risk_level} />
                </div>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Risk score <span className="font-semibold tabular-nums">{finding.risk_score}</span>
                {' · '}
                {finding.category}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export function PostureBanner({
  posture,
  summary,
}: {
  posture: string
  summary: string
}) {
  const tone =
    posture === 'IMPROVED'
      ? 'border-emerald-300 bg-gradient-to-br from-emerald-50 to-white text-emerald-950'
      : posture === 'WORSENED'
        ? 'border-rose-300 bg-gradient-to-br from-rose-50 to-white text-rose-950'
        : 'border-slate-300 bg-gradient-to-br from-slate-50 to-white text-slate-900'

  return (
    <div className={`rounded-xl border px-6 py-6 shadow-sm animate-fade-up ${tone}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.14em] opacity-80">
        Security posture
      </p>
      <p className="mt-2 text-4xl font-semibold tracking-tight">{posture}</p>
      <p className="mt-3 max-w-3xl text-sm leading-relaxed">{summary}</p>
    </div>
  )
}

export function CompareMetricCard({
  label,
  value,
  badge,
  subtitle,
  positive,
}: {
  label: string
  value: number | string
  badge?: string
  subtitle?: string
  positive?: boolean | null
}) {
  const valueClass =
    positive === true
      ? 'text-emerald-700'
      : positive === false
        ? 'text-rose-700'
        : 'text-slate-900'

  return (
    <div className="card-interactive rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-2 text-3xl font-semibold tabular-nums ${valueClass}`}>
        {typeof value === 'number' ? <AnimatedNumber value={value} /> : value}
      </p>
      {badge ? (
        <div className="mt-2">
          <RiskBadge value={badge} />
        </div>
      ) : null}
      {subtitle ? <p className="mt-2 text-sm text-slate-600">{subtitle}</p> : null}
    </div>
  )
}

export function CompareScanLink({ scanId }: { scanId: number }) {
  return (
    <Link
      to={`/scans/${scanId}/compare`}
      className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-800 hover:bg-slate-50 focus-ring"
    >
      Compare scan
    </Link>
  )
}
