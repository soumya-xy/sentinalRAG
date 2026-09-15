import type { ReactNode } from 'react'

export function Panel({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return <div className={`border border-border bg-surface ${className}`}>{children}</div>
}
