import { useNavigate } from 'react-router-dom'
import type { KeyboardEvent } from 'react'
import type { ScanHistoryItem } from '../types'
import { RiskBadge, StatusBadge } from './Badges'
import { formatDateTime, formatRiskScore } from '../utils/format'

interface ScanTableProps {
  scans: ScanHistoryItem[]
  onDelete?: (scan: ScanHistoryItem) => void
  deletingId?: number | null
}

export function ScanTable({ scans, onDelete, deletingId }: ScanTableProps) {
  const navigate = useNavigate()

  function openScan(id: number) {
    navigate(`/scans/${id}`)
  }

  function onRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, id: number) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openScan(id)
    }
  }

  return (
    <>
      <div className="hidden overflow-x-auto rounded-2xl border border-slate-200/90 bg-white shadow-sm md:block">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
          <thead className="bg-slate-50/90 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3 font-semibold">Scan name</th>
              <th className="px-4 py-3 font-semibold">Status</th>
              <th className="px-4 py-3 font-semibold">Risk level</th>
              <th className="px-4 py-3 font-semibold">Risk score</th>
              <th className="px-4 py-3 font-semibold">Findings</th>
              <th className="px-4 py-3 font-semibold">Created at</th>
              <th className="px-4 py-3 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {scans.map((scan) => (
              <tr
                key={scan.id}
                className="cursor-pointer transition-colors hover:bg-slate-50/90 focus-within:bg-slate-50"
                tabIndex={0}
                onClick={() => openScan(scan.id)}
                onKeyDown={(event) => onRowKeyDown(event, scan.id)}
              >
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-900">{scan.name}</div>
                  <div className="text-xs text-slate-500">
                    {scan.spec_metadata?.openapi_version
                      ? `OpenAPI ${scan.spec_metadata.openapi_version}`
                      : scan.spec_metadata?.title || 'OpenAPI spec'}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge value={scan.status} />
                </td>
                <td className="px-4 py-3">
                  <RiskBadge value={scan.risk_level || 'INFO'} />
                </td>
                <td className="px-4 py-3 tabular-nums text-slate-700">
                  {formatRiskScore(scan.overall_risk_score)}
                </td>
                <td className="px-4 py-3 tabular-nums text-slate-700">{scan.finding_count}</td>
                <td className="px-4 py-3 text-slate-600">{formatDateTime(scan.created_at)}</td>
                <td className="px-4 py-3" onClick={(event) => event.stopPropagation()}>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => openScan(scan.id)}
                      className="rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-slate-800 focus-ring"
                    >
                      View
                    </button>
                    {onDelete ? (
                      <button
                        type="button"
                        disabled={deletingId === scan.id}
                        onClick={() => onDelete(scan)}
                        className="rounded-lg border border-rose-300 px-2.5 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-50 focus-ring"
                      >
                        {deletingId === scan.id ? 'Deleting…' : 'Delete'}
                      </button>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="space-y-3 md:hidden">
        {scans.map((scan) => (
          <article
            key={`card-${scan.id}`}
            className="card-interactive rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className="font-semibold text-slate-900">{scan.name}</h3>
                <p className="mt-1 text-xs text-slate-500">{formatDateTime(scan.created_at)}</p>
              </div>
              <StatusBadge value={scan.status} />
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <RiskBadge value={scan.risk_level || 'INFO'} />
              <span className="text-xs text-slate-500">
                Score {formatRiskScore(scan.overall_risk_score)} · {scan.finding_count} findings
              </span>
            </div>
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                onClick={() => openScan(scan.id)}
                className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white focus-ring"
              >
                View
              </button>
              {onDelete ? (
                <button
                  type="button"
                  disabled={deletingId === scan.id}
                  onClick={() => onDelete(scan)}
                  className="rounded-lg border border-rose-300 px-3 py-1.5 text-xs font-medium text-rose-700 disabled:opacity-50 focus-ring"
                >
                  {deletingId === scan.id ? 'Deleting…' : 'Delete'}
                </button>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </>
  )
}
