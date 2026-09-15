import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { api } from './api/index.ts'
import { ApiError } from './api/client.ts'
import { clearSession, getStoredUser, getToken, persistSession } from './session.ts'
import type { User } from '../types/api.ts'

interface AuthContextValue {
  user: User | null
  ready: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const stored = getStoredUser()
    const token = getToken()
    if (!stored || !token) {
      setReady(true)
      return
    }
    setUser(stored)
    api
      .me()
      .then(setUser)
      .catch(() => {
        clearSession()
        setUser(null)
      })
      .finally(() => setReady(true))
  }, [])

  useEffect(() => {
    const onUnauthorized = () => setUser(null)
    window.addEventListener('sentinelrag:unauthorized', onUnauthorized)
    return () => window.removeEventListener('sentinelrag:unauthorized', onUnauthorized)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const response = await api.login({ email, password })
    persistSession(response.access_token, response.user)
    setUser(response.user)
  }, [])

  const register = useCallback(async (email: string, password: string, displayName: string) => {
    const response = await api.register({
      email,
      password,
      display_name: displayName,
    })
    persistSession(response.access_token, response.user)
    setUser(response.user)
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } catch (error) {
      if (!(error instanceof ApiError)) throw error
    } finally {
      clearSession()
      setUser(null)
    }
  }, [])

  const value = useMemo(
    () => ({ user, ready, login, register, logout }),
    [user, ready, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
