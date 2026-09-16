import { useEffect, useState } from 'react'

import { API_BASE } from '../lib/api/client.ts'
import { getToken } from '../lib/session.ts'

function resolveMediaUrl(path?: string | null): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
}

export function AuthenticatedImage({
  path,
  alt,
  className,
}: {
  path?: string | null
  alt: string
  className?: string
}) {
  const [src, setSrc] = useState('')

  useEffect(() => {
    const url = resolveMediaUrl(path)
    if (!url) {
      setSrc('')
      return
    }

    let objectUrl = ''
    let cancelled = false

    async function load() {
      const token = getToken()
      const headers = new Headers()
      if (token) headers.set('Authorization', `Bearer ${token}`)
      try {
        const response = await fetch(url, { headers })
        if (!response.ok) return
        const blob = await response.blob()
        objectUrl = URL.createObjectURL(blob)
        if (!cancelled) setSrc(objectUrl)
      } catch {
        if (!cancelled) setSrc('')
      }
    }

    void load()
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [path])

  if (!src) {
    return <div className={className} aria-hidden />
  }
  return <img src={src} alt={alt} className={className} />
}
