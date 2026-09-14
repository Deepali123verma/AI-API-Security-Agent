import type { ScanSummary } from '../types'
import { RiskBadge } from './Badges'
import { SEVERITY_ORDER } from '../utils/badges'

interface RiskSummaryProps {
  summary: Pick<
    ScanSummary,
    'critical' | 'high' | 'medium' | 'low' | 'info' | 'overall_risk_score' | 'risk_level' | 'finding_count'
  >
  compact?: boolean
}

export function RiskSummary({ summary, compact = false }: RiskSummaryProps) {
  const counts: Record<string, number> = {
    CRITICAL: summary.critical,
    HIGH: summary.high,
    MEDIUM: summary.medium,
    LOW: summary.low,
    INFO: summary.info,
  }

  return (
    <div className={`rounded-lg border border-slate-200 bg-white ${compact ? 'p-4' : 'p-5'}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-500">Overall risk</p>
          <div className="mt-1 flex items-center gap-3">
            <span className="text-3xl font-semibold tabular-nums text-slate-900">
              {summary.overall_risk_score}
            </span>
            <RiskBadge value={summary.risk_level} />
          </div>
          <p className="mt-1 text-sm text-slate-600">
            {summary.finding_count} finding{summary.finding_count === 1 ? '' : 's'}
          </p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-5">
        {SEVERITY_ORDER.map((level) => (
          <div key={level} className="rounded-md bg-slate-50 px-3 py-2 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              {level}
            </p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-slate-900">
              {counts[level] ?? 0}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
