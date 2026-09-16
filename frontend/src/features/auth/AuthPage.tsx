import { useMemo, useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'

import { Button } from '../../components/Button.tsx'
import { ErrorBanner } from '../../components/ErrorBanner.tsx'
import { Field } from '../../components/Field.tsx'
import { Input } from '../../components/Input.tsx'
import { ApiError } from '../../lib/api/client.ts'
import { useAuth } from '../../lib/auth.tsx'

type Mode = 'login' | 'register'

export function AuthPage() {
  const { user, ready, login, register } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const mode: Mode = params.get('mode') === 'register' ? 'register' : 'login'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const isLogin = mode === 'login'
  const nextMode = isLogin ? 'register' : 'login'

  const hint = useMemo(
    () => isLogin
      ? 'Enter your operator credentials to access the surveillance console.'
      : 'Create an operator account. Password must be at least 8 characters.',
    [isLogin],
  )

  if (ready && user) return <Navigate to="/workspace" replace />

  function validate(): boolean {
    const next: Record<string, string> = {}
    if (!email.trim()) next.email = 'Email is required'
    if (!password) next.password = 'Password is required'
    if (!isLogin) {
      if (password.length < 8) next.password = 'Use at least 8 characters'
      if (password !== confirm) next.confirm = 'Passwords do not match'
    }
    setFieldErrors(next)
    return Object.keys(next).length === 0
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)
    if (!validate()) return
    setSubmitting(true)
    try {
      if (isLogin) {
        await login(email.trim(), password)
      } else {
        await register(email.trim(), password, displayName.trim())
      }
      navigate('/workspace', { replace: true })
    } catch (error) {
      setFormError(error instanceof ApiError ? error.detail : 'Authentication failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-black text-[#EEEEEE] surveillance-grid flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-[#1a1a1a] bg-black/90 px-8 py-4">
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-[#CB2957] group-hover:bg-[#a8213e] transition-colors">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <rect x="0" y="3" width="9" height="8" rx="1.2" fill="white"/>
              <path d="M9 5.5l4.5-2.5v8l-4.5-2.5V5.5z" fill="white"/>
            </svg>
          </div>
          <span className="font-mono text-sm font-semibold tracking-tight">SENTINEL<span className="text-[#CB2957]">RAG</span></span>
        </Link>
        <span className="font-mono text-[10px] uppercase tracking-widest text-[#888888]">
          {isLogin ? 'Operator Authentication' : 'Account Registration'}
        </span>
      </header>

      {/* Body */}
      <main className="flex flex-1 items-center justify-center px-8 py-16">
        <div className="w-full max-w-md">
          {/* Card */}
          <div className="rounded-sm border border-[#1a1a1a] bg-[#050505] p-8">
            {/* Top accent line */}
            <div className="mb-8 h-px bg-gradient-to-r from-[#CB2957] to-transparent" />

            <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-[#CB2957]">
              {isLogin ? 'Secure Login' : 'New Operator'}
            </div>
            <h1 className="text-2xl font-bold text-[#EEEEEE]">
              {isLogin ? 'Welcome back.' : 'Create account.'}
            </h1>
            <p className="mt-2 text-xs text-[#999999] leading-relaxed">{hint}</p>

            <form onSubmit={onSubmit} className="mt-8 space-y-5" noValidate>
              {formError ? <ErrorBanner message={formError} /> : null}

              <Field label="Email address" error={fieldErrors.email}>
                <Input
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="operator@agency.gov"
                />
              </Field>

              {!isLogin ? (
                <Field label="Display name" hint="Optional — defaults to email prefix.">
                  <Input
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    autoComplete="name"
                    placeholder="Agent Smith"
                  />
                </Field>
              ) : null}

              <Field label="Password" error={fieldErrors.password}>
                <Input
                  type="password"
                  autoComplete={isLogin ? 'current-password' : 'new-password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </Field>

              {!isLogin ? (
                <Field label="Confirm password" error={fieldErrors.confirm}>
                  <Input
                    type="password"
                    autoComplete="new-password"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    placeholder="••••••••"
                  />
                </Field>
              ) : null}

              <div className="pt-2">
                <Button type="submit" disabled={submitting} className="w-full justify-center">
                  {submitting ? 'Authenticating…' : isLogin ? 'Access System' : 'Register Operator'}
                </Button>
              </div>
            </form>

            <div className="mt-6 border-t border-[#111111] pt-6 text-center">
              <Link
                to={`/auth?mode=${nextMode}`}
                className="font-mono text-xs text-[#999999] hover:text-[#CB2957] transition-colors uppercase tracking-wide"
              >
                {isLogin ? 'Need an account? Register →' : 'Already registered? Sign in →'}
              </Link>
            </div>
          </div>

          {/* Security notice */}
          <div className="mt-4 flex items-center justify-center gap-2">
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none" className="text-[#777777]">
              <path d="M5 1L1.5 2.5V5c0 1.93 1.5 3.5 3.5 3.5S8.5 6.93 8.5 5V2.5L5 1z" stroke="currentColor" strokeWidth="0.8"/>
            </svg>
            <span className="font-mono text-[10px] text-[#777777] uppercase tracking-widest">
              Secured · JWT Auth · Supabase
            </span>
          </div>
        </div>
      </main>
    </div>
  )
}
