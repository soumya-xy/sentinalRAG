import type { ReactNode } from 'react'

interface Props {
  label: string
  hint?: string
  error?: string
  children: ReactNode
}

export function Field({ label, hint, error, children }: Props) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-mono uppercase tracking-widest text-[#888888]">
        {label}
      </label>
      {children}
      {hint && !error && <p className="text-xs text-[#999999] font-mono">{hint}</p>}
      {error && <p className="text-xs text-[#CB2957] font-mono">{error}</p>}
    </div>
  )
}
