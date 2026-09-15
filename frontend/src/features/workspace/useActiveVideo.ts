import { useCallback, useEffect, useState } from 'react'

import { api, ApiError } from '../../lib/api/index.ts'
import { getActiveVideoId, setActiveVideoId } from '../../lib/session.ts'
import type { EventRecord, VideoRecord, VideoStatusResponse } from '../../types/api.ts'

export function useActiveVideo() {
  const [video, setVideo] = useState<VideoRecord | null>(null)
  const [status, setStatus] = useState<VideoStatusResponse | null>(null)
  const [events, setEvents] = useState<EventRecord[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const hydrate = useCallback(async (record: VideoRecord) => {
    setVideo(record)
    setActiveVideoId(record.video_id)
    const snapshot = await api.getVideoStatus(record.video_id)
    setStatus(snapshot)
    if (snapshot.status === 'ready') {
      const listed = await api.listEvents(record.video_id)
      setEvents(listed.events)
    } else {
      setEvents([])
    }
  }, [])

  const refresh = useCallback(async () => {
    setError(null)
    setLoading(true)
    try {
      const { videos } = await api.listVideos()
      const preferred = getActiveVideoId()
      const record =
        videos.find((item) => item.video_id === preferred) ?? videos[0] ?? null
      if (!record) {
        setVideo(null)
        setStatus(null)
        setEvents([])
        setActiveVideoId(null)
        return
      }
      await hydrate(record)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Failed to load video state')
    } finally {
      setLoading(false)
    }
  }, [hydrate])

  useEffect(() => {
    void refresh()
  }, [refresh])

  useEffect(() => {
    if (!video || !status) return
    if (status.status !== 'processing' && status.status !== 'uploaded') return
    const id = window.setInterval(() => {
      void api
        .getVideoStatus(video.video_id)
        .then(async (snapshot) => {
          setStatus(snapshot)
          setVideo((current) =>
            current ? { ...current, status: snapshot.status } : current,
          )
          if (snapshot.status === 'ready') {
            const listed = await api.listEvents(video.video_id)
            setEvents(listed.events)
          }
        })
        .catch((err: unknown) => {
          setError(err instanceof ApiError ? err.detail : 'Status poll failed')
        })
    }, 900)
    return () => window.clearInterval(id)
  }, [video, status])

  const adopt = useCallback(
    async (record: VideoRecord) => {
      setError(null)
      await hydrate(record)
    },
    [hydrate],
  )

  return { video, status, events, error, loading, refresh, adopt, setError }
}
