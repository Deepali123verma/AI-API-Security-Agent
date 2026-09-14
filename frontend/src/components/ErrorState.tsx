import { AlertTriangle } from 'lucide-react'

interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div
      className="rounded-lg border border-rose-200 bg-rose-50 px-5 py-8 text-center"
      role="alert"
    >
      <AlertTriangle className="mx-auto mb-3 h-8 w-8 text-rose-600" aria-hidden />
      <h2 className="text-base font-semibold text-rose-900">{title}</h2>
      <p className="mt-2 text-sm text-rose-800">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-md bg-rose-700 px-4 py-2 text-sm font-medium text-white hover:bg-rose-800"
        >
          Try again
        </button>
      ) : null}
    </div>
  )
}
