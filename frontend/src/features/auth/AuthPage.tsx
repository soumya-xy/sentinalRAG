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

  const title = mode === 'login' ? 'Sign in' : 'Create account'
  const nextMode = mode === 'login' ? 'register' : 'login'

  const hint = useMemo(
    () =>
      mode === 'login'
        ? 'Use the email and password you registered with Supabase Auth.'
        : 'Use a work email. Password must be at least 8 characters.',
    [mode],
  )

  if (ready && user) {
    return <Navigate to="/workspace" replace />
  }

  function validate(): boolean {
    const next: Record<string, string> = {}
    if (!email.trim()) next.email = 'Email is required'
    if (!password) next.password = 'Password is required'
    if (mode === 'register') {
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
      if (mode === 'login') {
        await login(email.trim(), password)
      } else {
        await register(email.trim(), password, displayName.trim())
      }
      navigate('/workspace', { replace: true })
    } catch (error) {
      const message = error instanceof ApiError ? error.detail : 'Authentication failed'
      setFormError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-base text-ink">
      <header className="flex items-end justify-between border-b border-border px-8 py-4">
        <Link to="/" className="text-lg font-semibold tracking-tight">
          SentinelRAG
        </Link>
        <span className="font-mono text-sm text-muted">Auth</span>
      </header>

      <main className="px-8 py-12">
        <h1 className="text-2xl font-medium">{title}</h1>
        <p className="mt-2 max-w-md text-sm text-muted">{hint}</p>

        <form onSubmit={onSubmit} className="mt-8 max-w-md space-y-4" noValidate>
          {formError ? <ErrorBanner message={formError} /> : null}

          <Field label="Email" error={fieldErrors.email}>
            <Input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </Field>

          {mode === 'register' ? (
            <Field label="Display name" hint="Optional. Defaults to the email local part.">
              <Input
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                autoComplete="name"
              />
            </Field>
          ) : null}

          <Field label="Password" error={fieldErrors.password}>
            <Input
              type="password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </Field>

          {mode === 'register' ? (
            <Field label="Confirm password" error={fieldErrors.confirm}>
              <Input
                type="password"
                autoComplete="new-password"
                value={confirm}
                onChange={(event) => setConfirm(event.target.value)}
              />
            </Field>
          ) : null}

          <div className="flex items-center gap-4 pt-2">
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Working…' : title}
            </Button>
            <Link
              to={`/auth?mode=${nextMode}`}
              className="text-sm text-muted hover:text-ink"
            >
              {mode === 'login' ? 'Need an account' : 'Already have an account'}
            </Link>
          </div>
        </form>
      </main>
    </div>
  )
}
