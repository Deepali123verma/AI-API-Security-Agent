import { Link } from 'react-router-dom'
import { RiskBadge } from './Badges'
import { SEVERITY_ORDER, normalizeSeverity, type SeverityKey } from '../utils/badges'
import { Tooltip } from './Tooltip'
import { AnimatedNumber } from './AnimatedNumber'

const BAR_COLORS: Record<SeverityKey, string> = {
  CRITICAL: 'bg-rose-600',
  HIGH: 'bg-orange-500',
  MEDIUM: 'bg-amber-400',
  LOW: 'bg-sky-500',
  INFO: 'bg-slate-400',
}

const GAUGE_COLORS: Record<SeverityKey, string> = {
  CRITICAL: '#e11d48',
  HIGH: '#f97316',
  MEDIUM: '#f59e0b',
  LOW: '#0ea5e9',
  INFO: '#94a3b8',
}

const DONUT_COLORS: Record<SeverityKey, string> = {
  CRITICAL: '#e11d48',
  HIGH: '#f97316',
  MEDIUM: '#f59e0b',
  LOW: '#0ea5e9',
  INFO: '#94a3b8',
}

interface SeverityDistributionProps {
  counts: Record<string, number>
  title?: string
  viewAllTo?: string
}

export function SeverityDistribution({
  counts,
  title = 'Findings by Severity',
  viewAllTo,
}: SeverityDistributionProps) {
  const total = SEVERITY_ORDER.reduce((sum, key) => sum + (counts[key] || 0), 0)
  const safeTotal = total || 1
  let cumulative = 0
  const segments = SEVERITY_ORDER.map((level) => {
    const value = counts[level] || 0
    const start = cumulative / safeTotal
    cumulative += value
    const end = cumulative / safeTotal
    return { level, value, start, end, pct: Math.round((value / safeTotal) * 100) }
  })

  const radius = 42
  const circumference = 2 * Math.PI * radius

  return (
    <div className="flex h-full flex-col rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm animate-fade-up">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-500">{title}</h2>
        {viewAllTo ? (
          <Link to={viewAllTo} className="text-sm font-medium text-sky-700 hover:text-sky-600">
            View all findings →
          </Link>
        ) : null}
      </div>

      <div className="mt-5 flex flex-1 flex-col items-center gap-6 lg:flex-row lg:items-center">
        <div className="relative shrink-0">
          <svg width="160" height="160" viewBox="0 0 160 160" aria-hidden>
            <circle cx="80" cy="80" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="16" />
            {total === 0 ? null : (
              segments.map((segment) => {
                if (!segment.value) return null
                const length = (segment.end - segment.start) * circumference
                const offset = circumference - segment.start * circumference
                return (
                  <circle
                    key={segment.level}
                    cx="80"
                    cy="80"
                    r={radius}
                    fill="none"
                    stroke={DONUT_COLORS[segment.level]}
                    strokeWidth="16"
                    strokeDasharray={`${length} ${circumference - length}`}
                    strokeDashoffset={offset}
                    transform="rotate(-90 80 80)"
                    className="transition-all duration-700 ease-out"
                  />
                )
              })
            )}
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <p className="text-2xl font-semibold tabular-nums text-slate-900">
              <AnimatedNumber value={total} />
            </p>
            <p className="text-[11px] uppercase tracking-wide text-slate-500">Findings</p>
          </div>
        </div>

        <div className="w-full flex-1 space-y-3">
          {SEVERITY_ORDER.map((level) => {
            const value = counts[level] || 0
            const pct = total === 0 ? 0 : Math.round((value / total) * 100)
            return (
              <div key={level}>
                <div className="mb-1 flex items-center justify-between gap-2 text-sm">
                  <RiskBadge value={level} />
                  <span className="tabular-nums text-slate-600">
                    {value} · {pct}%
                  </span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${BAR_COLORS[level]}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

interface RiskGaugeProps {
  score: number
  level?: string | null
  label?: string
  subtitle?: string
  metrics?: { label: string; value: number | string; to?: string }[]
  reportTo?: string
}

export function RiskGauge({
  score,
  level,
  label = 'Overall Security Posture',
  subtitle,
  metrics,
  reportTo,
}: RiskGaugeProps) {
  const clamped = Math.max(0, Math.min(100, Number.isFinite(score) ? score : 0))
  const severity = normalizeSeverity(level)
  const color = GAUGE_COLORS[severity]
  const radius = 58
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (clamped / 100) * circumference

  const postureCopy =
    subtitle ||
    (severity === 'CRITICAL' || severity === 'HIGH'
      ? 'Your API has findings that need attention.'
      : severity === 'MEDIUM'
        ? 'Moderate risk detected — review findings and remediations.'
        : severity === 'LOW'
          ? 'Low residual risk — continue monitoring regressions.'
          : 'No elevated risk signals in the selected scan context.')

  return (
    <div className="flex h-full flex-col rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm animate-fade-up">
      <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</h2>

      <div className="mt-4 flex flex-1 flex-col items-center justify-center">
        <svg width="168" height="168" viewBox="0 0 168 168" aria-hidden>
          <circle cx="84" cy="84" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="12" />
          <circle
            cx="84"
            cy="84"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform="rotate(-90 84 84)"
            className="transition-all duration-700 ease-out"
          />
          <text
            x="84"
            y="80"
            textAnchor="middle"
            style={{ fontSize: '34px', fontWeight: 600, fill: '#0f172a' }}
          >
            {clamped}
          </text>
          <text
            x="84"
            y="104"
            textAnchor="middle"
            style={{ fontSize: '11px', fontWeight: 600, fill: '#64748b', letterSpacing: '0.08em' }}
          >
            RISK SCORE
          </text>
        </svg>

        <Tooltip content="Deterministic Phase 5 score from the FastAPI backend (0–100).">
          <div className="mt-2">
            <RiskBadge value={severity} />
          </div>
        </Tooltip>
        <p className="mt-3 max-w-sm text-center text-sm text-slate-600">{postureCopy}</p>
      </div>

      {metrics && metrics.length > 0 ? (
        <div className="mt-6 grid grid-cols-3 gap-3 border-t border-slate-100 pt-5">
          {metrics.map((metric) => {
            const body = (
              <div className="text-center">
                <p className="text-[11px] uppercase tracking-wide text-slate-500">{metric.label}</p>
                <p className="mt-1 text-xl font-semibold tabular-nums text-slate-900">
                  {typeof metric.value === 'number' ? (
                    <AnimatedNumber value={metric.value} />
                  ) : (
                    metric.value
                  )}
                </p>
              </div>
            )
            return metric.to ? (
              <Link key={metric.label} to={metric.to} className="rounded-lg hover:bg-slate-50 focus-ring">
                {body}
              </Link>
            ) : (
              <div key={metric.label}>{body}</div>
            )
          })}
        </div>
      ) : null}

      {reportTo ? (
        <div className="mt-5 text-center">
          <Link to={reportTo} className="text-sm font-medium text-sky-700 hover:text-sky-600">
            View detailed report →
          </Link>
        </div>
      ) : null}
    </div>
  )
}
