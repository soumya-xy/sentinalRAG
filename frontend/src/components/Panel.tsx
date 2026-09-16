import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  className?: string
}

export function Panel({ children, className = '' }: Props) {
  return (
    <div className={`border border-[#1a1a1a] bg-[#0a0a0a] rounded-sm ${className}`}>
      {children}
    </div>
  )
}
