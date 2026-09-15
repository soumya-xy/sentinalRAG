import type { ReactNode } from 'react'

export function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string
  hint?: string
  error?: string
  children: ReactNode
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm text-muted">{label}</span>
      {children}
      {hint && !error ? <span className="mt-1.5 block text-sm text-muted">{hint}</span> : null}
      {error ? <span className="mt-1.5 block text-sm text-critical">{error}</span> : null}
    </label>
  )
}
