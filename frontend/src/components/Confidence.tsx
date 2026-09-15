import { confidenceTone, formatConfidence } from '../lib/format.ts'

const colors = {
  sage: 'text-sage',
  warning: 'text-warning',
  critical: 'text-critical',
}

export function Confidence({ score }: { score: number }) {
  return (
    <span className={`font-mono text-sm ${colors[confidenceTone(score)]}`}>
      {formatConfidence(score)}
    </span>
  )
}
