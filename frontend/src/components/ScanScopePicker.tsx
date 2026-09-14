import { useEffect, useState } from 'react'
import { listScans } from '../api/scans'
import type { ScanHistoryItem } from '../types'
import { getErrorMessage } from '../utils/errors'
import { StatusBadge, RiskBadge } from './Badges'
import { formatRiskScore } from '../utils/format'

interface ScanScopePickerProps {
  value: number | null
  onChange: (scanId: number) => void
  label?: string
  completedOnly?: boolean
}

export function ScanScopePicker({
  value,
  onChange,
  label = 'Active scan',
  completedOnly = false,
}: ScanScopePickerProps) {
  const [scans, setScans] = useState<ScanHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const response = await listScans({ page: 1, page_size: 100 })
        if (cancelled) return
        const items = completedOnly
          ? response.items.filter((item) => item.status.toUpperCase() === 'COMPLETED')
          : response.items
        setScans(items)
        if (value == null && items.length > 0) {
          onChange(items[0].id)
        }
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err, 'Unable to load scans.'))
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- hydrate once; parent owns value
  }, [completedOnly])

  const selected = scans.find((scan) => scan.id === value)

  return (
    <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-[240px] flex-1">
          <label htmlFor="scan-scope" className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            {label}
          </label>
          <select
            id="scan-scope"
            disabled={loading || scans.length === 0}
            value={value ?? ''}
            onChange={(e) => onChange(Number(e.target.value))}
            className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm focus-ring"
          >
            {scans.length === 0 ? <option value="">No scans available</option> : null}
            {scans.map((scan) => (
              <option key={scan.id} value={scan.id}>
                {scan.name} · #{scan.id} · {scan.status}
              </option>
            ))}
          </select>
        </div>
        {selected ? (
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge value={selected.status} />
            <RiskBadge value={selected.risk_level || 'INFO'} />
            <span className="text-xs text-slate-500">
              Score {formatRiskScore(selected.overall_risk_score)} · {selected.finding_count} findings
            </span>
          </div>
        ) : null}
      </div>
      {error ? <p className="mt-2 text-sm text-rose-700">{error}</p> : null}
      {loading ? <p className="mt-2 text-xs text-slate-500">Loading scans…</p> : null}
    </div>
  )
}
