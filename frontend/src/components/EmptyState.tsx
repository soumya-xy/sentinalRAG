import type { ReactNode } from 'react'

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string
  body: string
  action?: ReactNode
}) {
  return (
    <div className="max-w-xl">
      <h2 className="text-lg font-medium text-ink">{title}</h2>
      <p className="mt-2 text-muted">{body}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}
