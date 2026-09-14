import { methodBadgeClass, severityBadgeClass, statusBadgeClass } from '../utils/badges'

function Badge({
  label,
  className,
}: {
  label: string
  className: string
}) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ring-inset ${className}`}
    >
      {label}
    </span>
  )
}

export function SeverityBadge({ value }: { value?: string | null }) {
  const label = (value || 'INFO').toUpperCase()
  return <Badge label={label} className={severityBadgeClass(label)} />
}

export function RiskBadge({ value }: { value?: string | null }) {
  return <SeverityBadge value={value} />
}

export function StatusBadge({ value }: { value?: string | null }) {
  const label = (value || 'UNKNOWN').toUpperCase()
  return <Badge label={label} className={statusBadgeClass(label)} />
}

export function MethodBadge({ value }: { value?: string | null }) {
  const label = (value || '—').toUpperCase()
  return <Badge label={label} className={methodBadgeClass(label)} />
}
