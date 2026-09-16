import type { ReactNode } from 'react'

interface Props {
  title: string
  body: string
  action?: ReactNode
  children?: ReactNode
}

export function EmptyState({ title, body, action, children }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center px-8">
      {/* Camera icon */}
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-sm border border-[#222222] bg-[#0a0a0a]">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none" className="text-[#777777]">
          <rect x="2" y="7" width="16" height="14" rx="2" stroke="currentColor" strokeWidth="1.5"/>
          <path d="M18 11l7-4v14l-7-4V11z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
          <circle cx="10" cy="14" r="3" stroke="currentColor" strokeWidth="1.2"/>
        </svg>
      </div>
      <h3 className="text-sm font-semibold uppercase tracking-widest text-[#DDDDDD]">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-[#AAAAAA] leading-relaxed">{body}</p>
      {children}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
