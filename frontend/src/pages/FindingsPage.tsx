import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import {
  KeyRound,
  Lock,
  Database,
  Gauge,
  Settings2,
  Syringe,
  Search,
  ShieldAlert,
} from 'lucide-react'
import { listFindings } from '../api/scans'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { FindingCard } from '../components/FindingCard'
import { Pagination } from '../components/Pagination'
import { TableSkeleton } from '../components/Skeleton'
import type { Finding } from '../types'
import { getErrorMessage, getErrorStatus } from '../utils/errors'

const CATEGORY_ICONS: Record<string, typeof KeyRound> = {
  authentication: KeyRound,
  authorization: Lock,
  'sensitive data': Database,
  sensitive_data: Database,
  'rate limiting': Gauge,
  rate_limiting: Gauge,
  configuration: Settings2,
  injection: Syringe,
}

interface FindingsPageProps {
  forcedScanId?: number
  embed?: boolean
}

export function FindingsPage({ forcedScanId, embed = false }: FindingsPageProps = {}) {
  const { scanId } = useParams()
  const [searchParams] = useSearchParams()
  const id = forcedScanId ?? Number(scanId)
  const [items, setItems] = useState<Finding[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [severity, setSeverity] = useState(searchParams.get('severity') || '')
  const [category, setCategory] = useState('')
  const [search, setSearch] = useState('')
  const [sortDir, setSortDir] = useState<'desc' | 'asc'>('desc')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [errorStatus, setErrorStatus] = useState<number | null>(null)

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
      const response = await listFindings(id, {
        page,
        page_size: 50,
        severity: severity || undefined,
        category: category || undefined,
      })
      setItems(response.items)
      setTotal(response.total)
      setTotalPages(response.total_pages)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load findings.'))
      setErrorStatus(getErrorStatus(err))
    } finally {
      setLoading(false)
    }
  }, [id, page, severity, category])

  useEffect(() => {
    void load()
  }, [load])

  const categoryOptions = useMemo(() => {
    const set = new Set(items.map((item) => item.category).filter(Boolean))
    return Array.from(set).sort()
  }, [items])

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase()
    let next = items
    if (q) {
      next = next.filter((item) => {
        return (
          item.title.toLowerCase().includes(q) ||
          item.category.toLowerCase().includes(q) ||
          (item.endpoint || '').toLowerCase().includes(q)
        )
      })
    }
    return [...next].sort((a, b) =>
      sortDir === 'desc' ? b.risk_score - a.risk_score : a.risk_score - b.risk_score,
    )
  }, [items, search, sortDir])

  if (loading) {
    return <TableSkeleton rows={6} />
  }

  if (error) {
    return (
      <ErrorState
        title={errorStatus === 404 ? 'Scan not found' : 'Unable to load findings'}
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
            / Findings
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">
            Findings explorer
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Deterministic scanner output. Risk scores are calculated by the backend.
          </p>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3 rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm">
        <div className="min-w-[220px] flex-1">
          <label htmlFor="finding-search" className="mb-1 block text-xs font-medium uppercase text-slate-500">
            Search
          </label>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              id="finding-search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Title, category, endpoint…"
              className="w-full rounded-xl border border-slate-300 py-2 pl-9 pr-3 text-sm focus-ring"
            />
          </div>
        </div>
        <div>
          <label htmlFor="severity" className="mb-1 block text-xs font-medium uppercase text-slate-500">
            Severity
          </label>
          <select
            id="severity"
            value={severity}
            onChange={(e) => {
              setPage(1)
              setSeverity(e.target.value)
            }}
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus-ring"
          >
            <option value="">All</option>
            {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="category" className="mb-1 block text-xs font-medium uppercase text-slate-500">
            Category
          </label>
          <select
            id="category"
            value={category}
            onChange={(e) => {
              setPage(1)
              setCategory(e.target.value)
            }}
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus-ring"
          >
            <option value="">All</option>
            {categoryOptions.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="sort" className="mb-1 block text-xs font-medium uppercase text-slate-500">
            Sort by risk
          </label>
          <select
            id="sort"
            value={sortDir}
            onChange={(e) => setSortDir(e.target.value as 'asc' | 'desc')}
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus-ring"
          >
            <option value="desc">Highest first</option>
            <option value="asc">Lowest first</option>
          </select>
        </div>
      </div>

      {categoryOptions.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {categoryOptions.map((cat) => {
            const key = cat.toLowerCase()
            const Icon = CATEGORY_ICONS[key] || ShieldAlert
            return (
              <button
                key={cat}
                type="button"
                onClick={() => {
                  setPage(1)
                  setCategory(category === cat ? '' : cat)
                }}
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition ${
                  category === cat
                    ? 'border-sky-300 bg-sky-50 text-sky-800'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {cat}
              </button>
            )
          })}
        </div>
      ) : null}

      {visible.length === 0 ? (
        <EmptyState
          title={items.length === 0 ? 'No security findings detected' : 'No findings match your filters.'}
          description={
            items.length === 0
              ? 'Run a security scan from the scan detail page if this scan is still pending.'
              : 'Try clearing search or severity/category filters.'
          }
          action={
            <Link
              to={`/scans/${id}`}
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white focus-ring"
            >
              Back to scan
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {visible.map((finding) => (
            <FindingCard key={finding.id} finding={finding} scanId={id} expandable />
          ))}
        </div>
      )}

      <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />
    </div>
  )
}
