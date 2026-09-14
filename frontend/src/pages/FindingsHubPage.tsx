import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ScanScopePicker } from '../components/ScanScopePicker'
import { FindingsPage } from './FindingsPage'

export function FindingsHubPage() {
  const [scanId, setScanId] = useState<number | null>(null)

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Findings</h1>
        <p className="mt-1 text-sm text-slate-600">
          Explore deterministic security findings with severity, category, and risk sorting.
        </p>
      </div>

      <ScanScopePicker value={scanId} onChange={setScanId} label="Findings source scan" />

      {scanId ? (
        <div className="space-y-3">
          <p className="text-xs text-slate-500">
            Canonical route:{' '}
            <Link to={`/scans/${scanId}/findings`} className="text-sky-700 hover:underline">
              /scans/{scanId}/findings
            </Link>
          </p>
          <FindingsPage forcedScanId={scanId} embed />
        </div>
      ) : (
        <p className="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm text-slate-600">
          Select a scan to explore its findings.
        </p>
      )}
    </div>
  )
}
