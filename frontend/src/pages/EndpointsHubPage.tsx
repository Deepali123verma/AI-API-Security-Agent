import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ScanScopePicker } from '../components/ScanScopePicker'
import { EndpointsPage } from './EndpointsPage'

export function EndpointsHubPage() {
  const [scanId, setScanId] = useState<number | null>(null)

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">API Endpoints</h1>
        <p className="mt-1 text-sm text-slate-600">
          Professional API inventory across parsed OpenAPI operations.
        </p>
      </div>

      <ScanScopePicker value={scanId} onChange={setScanId} label="Scan inventory source" />

      {scanId ? (
        <div className="space-y-3">
          <p className="text-xs text-slate-500">
            Canonical route:{' '}
            <Link to={`/scans/${scanId}/endpoints`} className="text-sky-700 hover:underline">
              /scans/{scanId}/endpoints
            </Link>
          </p>
          <EndpointsPage forcedScanId={scanId} embed />
        </div>
      ) : (
        <p className="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm text-slate-600">
          Select a scan to browse its endpoint inventory.
        </p>
      )}
    </div>
  )
}
