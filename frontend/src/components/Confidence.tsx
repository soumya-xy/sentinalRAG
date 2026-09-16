export function Confidence({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = score >= 0.8 ? '#22c55e' : score >= 0.55 ? '#f59e0b' : '#CB2957'
  return (
    <span className="font-mono text-xs" style={{ color }}>
      {pct}%
    </span>
  )
}
