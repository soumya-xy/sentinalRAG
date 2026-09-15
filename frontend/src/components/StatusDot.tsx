type Tone = 'sage' | 'warning' | 'critical' | 'muted'

const tones: Record<Tone, string> = {
  sage: 'bg-sage',
  warning: 'bg-warning',
  critical: 'bg-critical',
  muted: 'bg-muted',
}

export function StatusDot({ tone, label }: { tone: Tone; label?: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className={`inline-block h-1.5 w-1.5 ${tones[tone]}`} />
      {label ? <span>{label}</span> : null}
    </span>
  )
}
