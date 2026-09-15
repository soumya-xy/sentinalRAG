import type { User } from '../types/api.ts'

const TOKEN_KEY = 'sentinelrag.token'
const USER_KEY = 'sentinelrag.user'
const VIDEO_KEY = 'sentinelrag.activeVideoId'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredUser(): User | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

export function persistSession(token: string, user: User): void {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getActiveVideoId(): string | null {
  return localStorage.getItem(VIDEO_KEY)
}

export function setActiveVideoId(videoId: string | null): void {
  if (videoId) localStorage.setItem(VIDEO_KEY, videoId)
  else localStorage.removeItem(VIDEO_KEY)
}
