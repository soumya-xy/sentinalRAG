import { Link } from 'react-router-dom'

import { Confidence } from '../../components/Confidence.tsx'
import { EmptyState } from '../../components/EmptyState.tsx'
import { resolveMediaUrl } from '../../lib/api/client.ts'
import type { EventRecord, VideoRecord, VideoStatusResponse } from '../../types/api.ts'

export function EventsTab({
  video,
  status,
  events,
}: {
  video: VideoRecord | null
  status: VideoStatusResponse | null
  events: EventRecord[]
}) {
  if (!video) {
    return (
      <EmptyState
        title="No events"
        body="Events appear after a video is ingested and the caption/index stages finish."
        action={
          <Link to="/workspace?tab=video" className="text-sm text-sage hover:text-ink">
            Open ingest
          </Link>
        }
      />
    )
  }

  if (status?.status !== 'ready') {
    return (
      <EmptyState
        title="Still indexing"
        body="The event list is written at the end of the batch pipeline. It stays empty until status is ready."
        action={
          <Link to="/workspace?tab=video" className="text-sm text-sage hover:text-ink">
            Watch processing
          </Link>
        }
      />
    )
  }

  if (events.length === 0) {
    return (
      <EmptyState
        title="Index is empty"
        body="Processing finished, but no events were stored for this video."
      />
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-medium">Indexed events</h1>
      <p className="mt-2 font-mono text-sm text-muted">
        {events.length} records  {video.video_id}  {video.camera_id}
      </p>

      <ul className="mt-8 divide-y divide-border border-y border-border">
        {events.map((event) => {
          const src = resolveMediaUrl(event.thumbnail_url)
          return (
            <li key={event.event_id} className="grid grid-cols-[10rem_1fr_11rem] gap-5 py-4">
              {src ? (
                <img
                  src={src}
                  alt={event.caption}
                  className="h-[90px] w-full border border-border object-cover"
                />
              ) : (
                <div className="flex h-[90px] items-center justify-center border border-border bg-surface font-mono text-xs text-muted">
                  no frame
                </div>
              )}
              <div className="min-w-0">
                <p className="max-w-prose">{event.caption}</p>
                <div className="mt-2 font-mono text-xs text-muted">
                  {event.detected_classes.join('  ')}
                </div>
                <div className="mt-1 font-mono text-xs text-muted">{event.event_id}</div>
              </div>
              <div className="text-right">
                <div className="font-mono text-sm">
                  {event.start_timestamp}–{event.end_timestamp}
                </div>
                <div className="mt-2">
                  <Confidence score={event.confidence_score} />
                </div>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
