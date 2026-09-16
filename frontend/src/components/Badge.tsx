interface Props {
  label: string
  variant?: 'default' | 'accent' | 'success' | 'warning' | 'danger'
}

const variants = {
  default: 'bg-[#1a1a1a] text-[#AAAAAA] border-[#333333]',
  accent:  'bg-[#CB2957]/15 text-[#CB2957] border-[#CB2957]/30',
  success: 'bg-[#22c55e]/10 text-[#22c55e] border-[#22c55e]/30',
  warning: 'bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/30',
  danger:  'bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/30',
}

export function Badge({ label, variant = 'default' }: Props) {
  return (
    <span className={`inline-flex items-center rounded-sm border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${variants[variant]}`}>
      {label}
    </span>
  )
}
