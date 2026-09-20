import { clearSession, getToken } from '../session.ts'

export const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
)

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function readDetail(payload: unknown): string {
  if (!payload || typeof payload !== 'object') return 'Request failed'
  const detail = (payload as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0] && typeof detail[0] === 'object') {
    const first = detail[0] as { msg?: string }
    if (first.msg) return first.msg
  }
  return 'Request failed'
}

export function resolveMediaUrl(path?: string | null): string {
  if (!path) return ''
  if (path.startsWith('data:')) return path
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  let fullUrl = `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
  const token = getToken()
  if (token && !fullUrl.includes('token=')) {
    fullUrl += `${fullUrl.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`
  }
  return fullUrl
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  const isForm = typeof FormData !== 'undefined' && options.body instanceof FormData
  if (!isForm && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  } catch {
    throw new ApiError(0, `Cannot reach SentinelRAG API at ${API_BASE}`)
  }

  if (response.status === 401) {
    clearSession()
    window.dispatchEvent(new Event('sentinelrag:unauthorized'))
  }

  if (response.status === 204) {
    return undefined as T
  }

  const payload: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(response.status, readDetail(payload))
  }
  return payload as T
}
