import { Link } from 'react-router-dom'

import { Badge } from '../../components/Badge.tsx'
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
        body="Events appear after a video is ingested and the full pipeline completes."
        action={
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#CB2957] border border-[#CB2957]/40 px-4 py-2 rounded-sm transition-all hover:bg-[#CB2957]/10">
            Ingest Footage →
          </Link>
        }
      />
    )
  }

  if (status?.status !== 'ready') {
    return (
      <EmptyState
        title="Still indexing"
        body="The event index is written at the final pipeline stage. It appears here once status is ready."
        action={
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#CB2957] border border-[#CB2957]/40 px-4 py-2 rounded-sm">
            Watch Pipeline →
          </Link>
        }
      />
    )
  }

  if (events.length === 0) {
    return (
      <EmptyState
        title="No events indexed"
        body="Processing finished but no events were stored for this video. Try re-uploading with a lower YOLO confidence threshold."
      />
    )
  }

  return (
    <div className="px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-[#CB2957]">Event Index</div>
        <h1 className="text-2xl font-bold text-[#EEEEEE]">Indexed Events</h1>
        <p className="mt-2 font-mono text-xs text-[#888888]">
          {events.length} events · {video.video_id} · {video.camera_id}
        </p>
      </div>

      {/* Stats bar */}
      <div className="mb-6 grid grid-cols-3 gap-px bg-[#1a1a1a] rounded-sm overflow-hidden border border-[#1a1a1a]">
        <div className="bg-[#050505] px-5 py-4">
          <div className="font-mono text-[9px] uppercase tracking-widest text-[#888888] mb-1">Total Events</div>
          <div className="font-mono text-2xl font-bold text-[#EEEEEE]">{events.length}</div>
        </div>
        <div className="bg-[#050505] px-5 py-4">
          <div className="font-mono text-[9px] uppercase tracking-widest text-[#888888] mb-1">Unique Classes</div>
          <div className="font-mono text-2xl font-bold text-[#EEEEEE]">
            {new Set(events.flatMap((e) => e.detected_classes)).size}
          </div>
        </div>
        <div className="bg-[#050505] px-5 py-4">
          <div className="font-mono text-[9px] uppercase tracking-widest text-[#888888] mb-1">Avg Confidence</div>
          <div className="font-mono text-2xl font-bold text-[#CB2957]">
            {Math.round((events.reduce((s, e) => s + e.confidence_score, 0) / events.length) * 100)}%
          </div>
        </div>
      </div>

      {/* Event list */}
      <div className="space-y-px rounded-sm border border-[#1a1a1a] overflow-hidden">
        {events.map((event, i) => {
          const src = resolveMediaUrl(event.thumbnail_url)
          const captionSource = event.caption_source

          return (
            <div
              key={event.event_id}
              className="group flex gap-5 bg-[#030303] px-5 py-4 hover:bg-[#050505] transition-colors border-b border-[#111111] last:border-0"
            >
              {/* Row number */}
              <div className="shrink-0 w-7 pt-0.5">
                <span className="font-mono text-[10px] text-[#777777]">{String(i + 1).padStart(2, '0')}</span>
              </div>

              {/* Thumbnail */}
              <div className="shrink-0 relative">
                {src ? (
                  <div className="relative overflow-hidden rounded-sm">
                    <img
                      src={src}
                      alt={event.caption}
                      className="h-[72px] w-[108px] object-cover border border-[#222222]"
                    />
                    {/* REC badge */}
                    <div className="absolute top-1 left-1 flex items-center gap-1">
                      <span className="h-1 w-1 rounded-full bg-[#CB2957]" />
                    </div>
                  </div>
                ) : (
                  <div className="flex h-[72px] w-[108px] items-center justify-center border border-[#1a1a1a] bg-[#0a0a0a] rounded-sm">
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" className="text-[#777777]">
                      <rect x="1.5" y="4.5" width="10" height="9" rx="1.2" stroke="currentColor" strokeWidth="1.1"/>
                      <path d="M11.5 7.5l5-3v9l-5-3" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round"/>
                    </svg>
                  </div>
                )}
              </div>

              {/* Caption & classes */}
              <div className="flex-1 min-w-0 space-y-2">
                <p className="text-sm text-[#CCCCCC] leading-relaxed line-clamp-2">{event.caption}</p>
                <div className="flex flex-wrap gap-1.5">
                  {event.detected_classes.map((cls) => (
                    <Badge key={cls} label={cls} variant="default" />
                  ))}
                  {captionSource === 'vlm' && (
                    <Badge label="VLM Caption" variant="accent" />
                  )}
                </div>
                <div className="font-mono text-[9px] text-[#777777] truncate">{event.event_id}</div>
              </div>

              {/* Timestamp & confidence */}
              <div className="shrink-0 text-right space-y-2">
                <div className="font-mono text-xs text-[#DDDDDD] tabular-nums">
                  {event.start_timestamp}
                </div>
                <div className="font-mono text-[10px] text-[#888888] tabular-nums">
                  → {event.end_timestamp}
                </div>
                <Confidence score={event.confidence_score} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
