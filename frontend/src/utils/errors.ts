import { AxiosError } from 'axios'
import type { ApiErrorBody } from '../types'

export class AppError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'AppError'
    this.status = status
  }
}

function detailToMessage(detail: ApiErrorBody['detail'], fallback: string): string {
  if (!detail) {
    return fallback
  }
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg || JSON.stringify(item))
      .filter(Boolean)
      .join('; ')
  }
  if (typeof detail === 'object' && 'message' in detail) {
    return String((detail as { message: unknown }).message)
  }
  return fallback
}

export function getErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (error instanceof AppError) {
    return error.message
  }
  if (error instanceof AxiosError) {
    const status = error.response?.status
    const body = error.response?.data as ApiErrorBody | undefined
    const detail = detailToMessage(body?.detail, fallback)

    if (status === 401) {
      return 'Your session has expired. Please sign in again.'
    }
    if (status === 403) {
      return 'You do not have permission to access this resource.'
    }
    if (status === 404) {
      return detail || 'The requested resource was not found.'
    }
    if (status === 409) {
      return detail || 'This request conflicts with the current state.'
    }
    if (status === 413) {
      return detail || 'Uploaded file exceeds the maximum allowed size (5 MB).'
    }
    if (status === 422) {
      return detail || 'Validation failed. Check your input and try again.'
    }
    if (status === 429) {
      return detail || 'Too many requests. Please wait and try again.'
    }
    if (status === 503) {
      return (
        detail ||
        'AI analysis is temporarily unavailable. The deterministic security finding is still available.'
      )
    }
    if (status && status >= 500) {
      return detail || 'A server error occurred. Please try again.'
    }
    if (status && status >= 400) {
      return detail || fallback
    }
    return error.message || fallback
  }
  if (error instanceof Error) {
    return error.message
  }
  return fallback
}

export function getErrorStatus(error: unknown): number | null {
  if (error instanceof AppError) {
    return error.status
  }
  if (error instanceof AxiosError) {
    return error.response?.status ?? null
  }
  return null
}

export function isAiUnavailable(error: unknown): boolean {
  return getErrorStatus(error) === 503
}
