import { Link, useNavigate } from 'react-router-dom'
import type { EndpointHistoryItem } from '../types'
import { MethodBadge } from './Badges'

interface EndpointTableProps {
  endpoints: EndpointHistoryItem[]
  scanId?: number
}

export function EndpointTable({ endpoints, scanId }: EndpointTableProps) {
  const navigate = useNavigate()

  return (
    <>
      <div className="hidden overflow-x-auto rounded-2xl border border-slate-200/90 bg-white shadow-sm md:block">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
          <thead className="bg-slate-50/90 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3 font-semibold">Method</th>
              <th className="px-4 py-3 font-semibold">Endpoint</th>
              <th className="px-4 py-3 font-semibold">Summary</th>
              <th className="hidden px-4 py-3 font-semibold lg:table-cell">Tags</th>
              <th className="px-4 py-3 font-semibold">Findings</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {endpoints.map((endpoint) => {
              const clickable = Boolean(scanId && endpoint.finding_count > 0)
              return (
                <tr
                  key={endpoint.id}
                  className={`transition-colors hover:bg-slate-50/90 ${clickable ? 'cursor-pointer' : ''}`}
                  onClick={() => {
                    if (scanId && endpoint.finding_count > 0) {
                      navigate(`/scans/${scanId}/findings`)
                    }
                  }}
                >
                  <td className="px-4 py-3">
                    <MethodBadge value={endpoint.method} />
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-800 sm:text-sm">
                    {endpoint.path}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{endpoint.summary || '—'}</td>
                  <td className="hidden px-4 py-3 text-slate-600 lg:table-cell">
                    {endpoint.tags?.length ? endpoint.tags.join(', ') : '—'}
                  </td>
                  <td className="px-4 py-3 tabular-nums text-slate-700">{endpoint.finding_count}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="space-y-3 md:hidden">
        {endpoints.map((endpoint) => (
          <div
            key={`card-${endpoint.id}`}
            className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="flex items-center justify-between gap-2">
              <MethodBadge value={endpoint.method} />
              <span className="text-xs text-slate-500">{endpoint.finding_count} findings</span>
            </div>
            <p className="mt-2 font-mono text-xs text-slate-800">{endpoint.path}</p>
            <p className="mt-1 text-sm text-slate-600">{endpoint.summary || '—'}</p>
            {scanId && endpoint.finding_count > 0 ? (
              <Link
                to={`/scans/${scanId}/findings`}
                className="mt-2 inline-block text-xs font-medium text-sky-700"
              >
                View findings →
              </Link>
            ) : null}
          </div>
        ))}
      </div>
    </>
  )
}
