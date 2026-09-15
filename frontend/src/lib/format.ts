export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatConfidence(score: number): string {
  return score.toFixed(2)
}

export function confidenceTone(score: number): 'sage' | 'warning' | 'critical' {
  if (score >= 0.8) return 'sage'
  if (score >= 0.55) return 'warning'
  return 'critical'
}

export function clockLabel(date: Date): string {
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  const ss = String(date.getSeconds()).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
}
