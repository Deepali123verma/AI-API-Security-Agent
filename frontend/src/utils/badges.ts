const SEVERITY_ORDER = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'] as const

export type SeverityKey = (typeof SEVERITY_ORDER)[number]

export function normalizeSeverity(value?: string | null): SeverityKey {
  const upper = (value || 'INFO').toUpperCase()
  if ((SEVERITY_ORDER as readonly string[]).includes(upper)) {
    return upper as SeverityKey
  }
  return 'INFO'
}

export function severityBadgeClass(value?: string | null): string {
  switch (normalizeSeverity(value)) {
    case 'CRITICAL':
      return 'bg-rose-100 text-rose-800 ring-rose-200'
    case 'HIGH':
      return 'bg-orange-100 text-orange-800 ring-orange-200'
    case 'MEDIUM':
      return 'bg-amber-100 text-amber-900 ring-amber-200'
    case 'LOW':
      return 'bg-sky-100 text-sky-800 ring-sky-200'
    default:
      return 'bg-slate-100 text-slate-700 ring-slate-200'
  }
}

export function statusBadgeClass(status?: string | null): string {
  switch ((status || '').toUpperCase()) {
    case 'COMPLETED':
      return 'bg-emerald-100 text-emerald-800 ring-emerald-200'
    case 'PENDING':
      return 'bg-amber-100 text-amber-900 ring-amber-200'
    case 'PARSING':
      return 'bg-sky-100 text-sky-800 ring-sky-200'
    case 'FAILED':
      return 'bg-rose-100 text-rose-800 ring-rose-200'
    default:
      return 'bg-slate-100 text-slate-700 ring-slate-200'
  }
}


export function methodBadgeClass(method?: string | null): string {
  switch ((method || '').toUpperCase()) {
    case 'GET':
      return 'bg-emerald-50 text-emerald-700 ring-emerald-200'
    case 'POST':
      return 'bg-sky-50 text-sky-700 ring-sky-200'
    case 'PUT':
      return 'bg-amber-50 text-amber-800 ring-amber-200'
    case 'PATCH':
      return 'bg-orange-50 text-orange-800 ring-orange-200'
    case 'DELETE':
      return 'bg-rose-50 text-rose-700 ring-rose-200'
    default:
      return 'bg-slate-50 text-slate-700 ring-slate-200'
  }
}

export { SEVERITY_ORDER }
