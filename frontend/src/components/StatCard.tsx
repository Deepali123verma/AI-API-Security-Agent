import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'
import { ArrowUpRight } from 'lucide-react'
import { AnimatedNumber } from './AnimatedNumber'
import { Tooltip } from './Tooltip'

interface StatCardProps {
  label: string
  value: number
  hint?: string
  to?: string
  icon?: ReactNode
  accent?: string
}

export function StatCard({
  label,
  value,
  hint,
  to,
  icon,
  accent = 'border-slate-200/90',
}: StatCardProps) {
  const content = (
    <div
      className={`card-interactive group relative overflow-hidden rounded-2xl border bg-white p-5 shadow-sm ${accent} ${
        to ? 'cursor-pointer' : ''
      }`}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-300/60 to-transparent opacity-0 transition group-hover:opacity-100" />
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
            <AnimatedNumber value={value} />
          </p>
          {hint ? <p className="mt-2 text-xs leading-relaxed text-slate-500">{hint}</p> : null}
        </div>
        <div className="flex flex-col items-end gap-3">
          {icon ? (
            <div className="rounded-xl bg-slate-50 p-2.5 text-slate-600 ring-1 ring-slate-100">{icon}</div>
          ) : null}
          {to ? (
            <ArrowUpRight className="h-4 w-4 text-slate-400 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-sky-600" />
          ) : null}
        </div>
      </div>
    </div>
  )

  if (to) {
    return (
      <Tooltip content={hint || `Open ${label.toLowerCase()}`}>
        <Link to={to} className="block rounded-2xl focus-ring">
          {content}
        </Link>
      </Tooltip>
    )
  }

  return content
}
