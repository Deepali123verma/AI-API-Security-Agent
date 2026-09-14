import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Search } from 'lucide-react'
import { listEndpoints } from '../api/scans'
import { EmptyState } from '../components/EmptyState'
import { EndpointTable } from '../components/EndpointTable'
import { ErrorState } from '../components/ErrorState'
import { Pagination } from '../components/Pagination'
import { TableSkeleton } from '../components/Skeleton'
import type { EndpointHistoryItem } from '../types'
import { getErrorMessage, getErrorStatus } from '../utils/errors'

interface EndpointsPageProps {
  forcedScanId?: number
  embed?: boolean
}

export function EndpointsPage({ forcedScanId, embed = false }: EndpointsPageProps = {}) {
  const { scanId } = useParams()
  const id = forcedScanId ?? Number(scanId)
  const [items, setItems] = useState<EndpointHistoryItem[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [errorStatus, setErrorStatus] = useState<number | null>(null)
  const [query, setQuery] = useState('')
  const [methodFilter, setMethodFilter] = useState('')

  useEffect(() => {
    setPage(1)
  }, [id])

  const load = useCallback(async () => {
    if (!Number.isFinite(id)) {
      setError('Invalid scan id.')
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await listEndpoints(id, page, 50)
      setItems(response.items)
      setTotal(response.total)
      setTotalPages(response.total_pages)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load endpoints.'))
      setErrorStatus(getErrorStatus(err))
    } finally {
      setLoading(false)
    }
  }, [id, page])

  useEffect(() => {
    void load()
  }, [load])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return items.filter((item) => {
      if (methodFilter && item.method.toUpperCase() !== methodFilter) {
        return false
      }
      if (!q) {
        return true
      }
      return (
        item.path.toLowerCase().includes(q) ||
        (item.summary || '').toLowerCase().includes(q) ||
        (item.operation_id || '').toLowerCase().includes(q) ||
        item.tags.some((tag) => tag.toLowerCase().includes(q))
      )
    })
  }, [items, query, methodFilter])

  if (loading) {
    return <TableSkeleton rows={6} />
  }

  if (error) {
    return (
      <ErrorState
        title={errorStatus === 404 ? 'Scan not found' : 'Unable to load endpoints'}
        message={error}
        onRetry={() => void load()}
      />
    )
  }

  return (
    <div className={`space-y-6 ${embed ? '' : 'animate-fade-up'}`}>
      {!embed ? (
        <div>
          <p className="text-sm text-slate-500">
            <Link to={`/scans/${id}`} className="text-sky-700 hover:underline">
              Scan #{id}
            </Link>{' '}
            / Endpoints
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">
            API inventory
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Parsed OpenAPI operations with finding counts from the FastAPI backend.
          </p>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3 rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm">
        <div className="relative min-w-[240px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="search"
            placeholder="Search path, summary, tag…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full rounded-xl border border-slate-300 py-2 pl-9 pr-3 text-sm focus-ring"
          />
        </div>
        <select
          value={methodFilter}
          onChange={(e) => setMethodFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus-ring"
        >
          <option value="">All methods</option>
          {['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'].map((method) => (
            <option key={method} value={method}>
              {method}
            </option>
          ))}
        </select>
        <Link
          to={`/scans/${id}/findings`}
          className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50 focus-ring"
        >
          Related findings
        </Link>
      </div>

      {items.length === 0 ? (
        <EmptyState
          title="No endpoints discovered"
          description="This scan has no parsed endpoints yet."
        />
      ) : filtered.length === 0 ? (
        <EmptyState title="No endpoints match your filter on this page." />
      ) : (
        <EndpointTable endpoints={filtered} scanId={id} />
      )}

      <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />
    </div>
  )
}
