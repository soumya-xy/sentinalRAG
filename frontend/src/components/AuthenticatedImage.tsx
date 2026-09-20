import { useEffect, useState } from 'react'
import { resolveMediaUrl } from '../lib/api/client.ts'
import { getToken } from '../lib/session.ts'

export function AuthenticatedImage({
  path,
  alt,
  className = '',
}: {
  path?: string | null
  alt: string
  className?: string
}) {
  const [src, setSrc] = useState<string>(() => resolveMediaUrl(path))
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    const url = resolveMediaUrl(path)
    if (!url) {
      setSrc('')
      setLoading(false)
      setError(true)
      return
    }

    setSrc(url)
    setError(false)
    setLoading(true)

    let objectUrl = ''
    let cancelled = false

    async function load() {
      const token = getToken()
      const headers = new Headers()
      if (token) headers.set('Authorization', `Bearer ${token}`)
      try {
        const response = await fetch(url, { headers })
        if (response.ok) {
          const blob = await response.blob()
          objectUrl = URL.createObjectURL(blob)
          if (!cancelled) {
            setSrc(objectUrl)
            setLoading(false)
          }
        } else {
          if (!cancelled) {
            // Keep direct url with token parameter as fallback
            setLoading(false)
          }
        }
      } catch {
        if (!cancelled) setLoading(false)
      }
    }

    void load()

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [path])

  if (error || !src) {
    return (
      <div className={`flex flex-col items-center justify-center bg-[#0d0d0d] border border-[#222222] text-[#888888] ${className}`}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21 15 16 10 5 21"/>
        </svg>
        <span className="text-[10px] font-mono mt-1 text-[#666666]">No Frame</span>
      </div>
    )
  }

  return (
    <div className={`relative overflow-hidden ${className}`}>
      <img
        src={src}
        alt={alt}
        className="h-full w-full object-cover transition-opacity duration-200"
        onError={() => setError(true)}
      />
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-[1px]">
          <span className="h-2 w-2 rounded-full bg-[#CB2957] animate-ping" />
        </div>
      )}
    </div>
  )
}
