import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { clearToken, getToken } from './token'

/**
 * Resolve the API base URL.
 * - Local dev (no env): http://localhost:8000
 * - Production same-origin deploy: leave VITE_API_BASE_URL empty so requests use the public app URL
 * - Split hosting: set VITE_API_BASE_URL to the absolute API origin
 */
function resolveApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL
  if (typeof configured === 'string' && configured.trim() !== '') {
    return configured.trim().replace(/\/$/, '')
  }
  if (import.meta.env.PROD) {
    return ''
  }
  return 'http://localhost:8000'
}

const baseURL = resolveApiBaseUrl()

export const api = axios.create({
  baseURL,
  headers: {
    Accept: 'application/json',
  },
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

type UnauthorizedHandler = () => void

let onUnauthorized: UnauthorizedHandler | null = null

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  onUnauthorized = handler
}

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      clearToken()
      onUnauthorized?.()
    }
    return Promise.reject(error)
  },
)

export function getApiBaseUrl(): string {
  return baseURL
}
