type Tone = 'success' | 'warning' | 'danger' | 'muted' | 'accent'

const toneMap: Record<Tone, { dot: string; text: string }> = {
  success: { dot: 'bg-[#22c55e]', text: 'text-[#22c55e]' },
  warning: { dot: 'bg-[#f59e0b]', text: 'text-[#f59e0b]' },
  danger:  { dot: 'bg-[#ef4444]', text: 'text-[#ef4444]' },
  accent:  { dot: 'bg-[#CB2957]', text: 'text-[#CB2957]' },
  muted:   { dot: 'bg-[#555555]', text: 'text-[#AAAAAA]' },
}

interface Props {
  tone: Tone
  label: string
  pulse?: boolean
}

export function StatusDot({ tone, label, pulse = false }: Props) {
  const { dot, text } = toneMap[tone]
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className={`inline-block h-1.5 w-1.5 rounded-full ${dot} ${pulse ? 'pulse-dot' : ''}`}
      />
      <span className={`font-mono text-xs uppercase tracking-wide ${text}`}>{label}</span>
    </span>
  )
}

export function statusToTone(status: string | undefined): Tone {
  if (status === 'ready') return 'success'
  if (status === 'processing' || status === 'uploaded') return 'warning'
  if (status === 'failed') return 'danger'
  return 'muted'
}
