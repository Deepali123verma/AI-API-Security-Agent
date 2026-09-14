import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Search, Upload } from 'lucide-react'
import { createScan, deleteScan, listScans } from '../api/scans'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { Pagination } from '../components/Pagination'
import { ScanTable } from '../components/ScanTable'
import { TableSkeleton } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'
import type { ScanHistoryItem } from '../types'
import { getErrorMessage } from '../utils/errors'

const MAX_UPLOAD_BYTES = 5 * 1024 * 1024

export function ScansPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const [searchParams] = useSearchParams()
  const [scans, setScans] = useState<ScanHistoryItem[]>([])
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [status, setStatus] = useState(searchParams.get('status') || '')
  const [riskLevel, setRiskLevel] = useState(searchParams.get('risk_level') || '')
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [pendingDelete, setPendingDelete] = useState<ScanHistoryItem | null>(null)

  const [file, setFile] = useState<File | null>(null)
  const [scanName, setScanName] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await listScans({
        page,
        page_size: pageSize,
        status: status || undefined,
        risk_level: riskLevel || undefined,
      })
      setScans(response.items)
      setTotal(response.total)
      setTotalPages(response.total_pages)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load scan history.'))
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, status, riskLevel])

  useEffect(() => {
    void load()
  }, [load])

  const filteredScans = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) {
      return scans
    }
    return scans.filter((scan) => {
      return (
        scan.name.toLowerCase().includes(q) ||
        (scan.spec_metadata?.title || '').toLowerCase().includes(q) ||
        String(scan.id).includes(q)
      )
    })
  }, [scans, query])

  async function handleUpload(event: FormEvent) {
    event.preventDefault()
    setUploadError(null)
    if (!file) {
      setUploadError('Select a JSON or YAML OpenAPI file.')
      return
    }
    const lower = file.name.toLowerCase()
    if (!(lower.endsWith('.json') || lower.endsWith('.yaml') || lower.endsWith('.yml'))) {
      setUploadError('Unsupported file type. Use .json, .yaml, or .yml.')
      return
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setUploadError('File exceeds the 5 MB backend upload limit.')
      return
    }

    setUploading(true)
    try {
      const created = await createScan(file, scanName || undefined)
      setFile(null)
      setScanName('')
      toast.success('OpenAPI uploaded. Opening scan detail…')
      navigate(`/scans/${created.scan_id}`)
    } catch (err) {
      const message = getErrorMessage(err, 'Upload failed.')
      setUploadError(message)
      toast.error(message)
    } finally {
      setUploading(false)
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) {
      return
    }
    setDeletingId(pendingDelete.id)
    try {
      await deleteScan(pendingDelete.id)
      toast.success(`Deleted scan “${pendingDelete.name}”.`)
      setPendingDelete(null)
      await load()
    } catch (err) {
      const message = getErrorMessage(err, 'Unable to delete scan.')
      setError(message)
      toast.error(message)
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Scans</h1>
          <p className="mt-1 text-sm text-slate-600">
            Upload OpenAPI specs and review deterministic security scan results.
          </p>
        </div>
        <a
          href="#new-scan"
          className="inline-flex items-center rounded-xl bg-sky-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-sky-600 focus-ring"
        >
          + New Scan
        </a>
      </div>

      <section
        id="new-scan"
        className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm"
      >
        <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
          <Upload className="h-5 w-5 text-sky-700" aria-hidden />
          Upload OpenAPI specification
        </h2>
        <form onSubmit={handleUpload} className="mt-4 grid gap-4 md:grid-cols-[1fr_1fr_auto]">
          <div>
            <label htmlFor="scan-name" className="mb-1 block text-sm font-medium text-slate-700">
              Scan name (optional)
            </label>
            <input
              id="scan-name"
              value={scanName}
              onChange={(e) => setScanName(e.target.value)}
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus-ring"
              placeholder="e.g. Payments API v2"
            />
          </div>
          <div>
            <label htmlFor="scan-file" className="mb-1 block text-sm font-medium text-slate-700">
              Spec file (JSON / YAML)
            </label>
            <input
              id="scan-file"
              type="file"
              accept=".json,.yaml,.yml,application/json,text/yaml"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-900 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white"
            />
            {file ? (
              <p className="mt-1 text-xs text-slate-500">
                Selected: {file.name} ({Math.round(file.size / 1024)} KB)
              </p>
            ) : null}
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={uploading}
              className="w-full rounded-xl bg-sky-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-sky-600 disabled:opacity-60 focus-ring md:w-auto"
            >
              {uploading ? 'Uploading…' : 'Start scan'}
            </button>
          </div>
        </form>
        {uploadError ? (
          <p className="mt-3 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800" role="alert">
            {uploadError}
          </p>
        ) : null}
      </section>

      <section id="history" className="space-y-4">
        <div className="flex flex-wrap gap-3 rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm">
          <div className="min-w-[220px] flex-1">
            <label htmlFor="scan-search" className="mb-1 block text-xs font-medium uppercase text-slate-500">
              Search
            </label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                id="scan-search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Name, title, or id…"
                className="w-full rounded-xl border border-slate-300 py-2 pl-9 pr-3 text-sm focus-ring"
              />
            </div>
          </div>
          <div>
            <label htmlFor="status-filter" className="mb-1 block text-xs font-medium uppercase text-slate-500">
              All Statuses
            </label>
            <select
              id="status-filter"
              value={status}
              onChange={(e) => {
                setPage(1)
                setStatus(e.target.value)
              }}
              className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus-ring"
            >
              <option value="">All Statuses</option>
              <option value="PENDING">PENDING</option>
              <option value="PARSING">PARSING</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="FAILED">FAILED</option>
            </select>
          </div>
          <div>
            <label htmlFor="risk-filter" className="mb-1 block text-xs font-medium uppercase text-slate-500">
              Risk level
            </label>
            <select
              id="risk-filter"
              value={riskLevel}
              onChange={(e) => {
                setPage(1)
                setRiskLevel(e.target.value)
              }}
              className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus-ring"
            >
              <option value="">All</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
              <option value="INFO">INFO</option>
            </select>
          </div>
        </div>

        {loading ? <TableSkeleton /> : null}
        {!loading && error ? (
          <ErrorState title="Unable to load scan history" message={error} onRetry={() => void load()} />
        ) : null}
        {!loading && !error && filteredScans.length === 0 ? (
          <EmptyState
            title={scans.length === 0 ? 'No scans yet.' : 'No scans match your filters.'}
            description={
              scans.length === 0
                ? 'Upload an OpenAPI specification to start your first security scan.'
                : 'Try clearing search or backend filters.'
            }
          />
        ) : null}
        {!loading && !error && filteredScans.length > 0 ? (
          <>
            <ScanTable
              scans={filteredScans}
              onDelete={(scan) => setPendingDelete(scan)}
              deletingId={deletingId}
            />
            <Pagination
              page={page}
              totalPages={totalPages}
              total={total}
              onPageChange={setPage}
            />
          </>
        ) : null}
        {!loading && !error ? (
          <p className="text-xs text-slate-500">
            Prefer the{' '}
            <Link to="/dashboard" className="text-sky-700 hover:underline">
              dashboard
            </Link>{' '}
            for a summary view.
          </p>
        ) : null}
      </section>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Delete scan?"
        description={
          pendingDelete
            ? `This permanently removes “${pendingDelete.name}” and all related findings and endpoints.`
            : ''
        }
        confirmLabel="Delete scan"
        busy={deletingId != null}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => void confirmDelete()}
      />
    </div>
  )
}
