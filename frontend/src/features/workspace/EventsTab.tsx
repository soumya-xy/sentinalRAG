import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Badge } from '../../components/Badge.tsx'
import { Confidence } from '../../components/Confidence.tsx'
import { EmptyState } from '../../components/EmptyState.tsx'
import { AuthenticatedImage } from '../../components/AuthenticatedImage.tsx'
import { ProcessTrail } from '../../components/ProcessTrail.tsx'
import { captionSourceLabel, captionSourceShort } from '../../lib/pipelineCopy.ts'
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
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [zoomedUrl, setZoomedUrl] = useState<string | null>(null)

  if (!video) {
    return (
      <EmptyState
        title="No event index yet"
        body="This list is the searchable memory of a video: one row per tracked object, with a caption written at ingest. Upload footage to create it."
        action={
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-sans text-xs font-semibold uppercase tracking-wider text-[#CB2957] border border-[#CB2957]/40 px-4 py-2 rounded-md transition-all hover:bg-[#CB2957]/10">
            Ingest Footage →
          </Link>
        }
      >
        <ProcessTrail
          steps={[
            { title: 'Detect', body: 'YOLO11 boxes on sampled stills.' },
            { title: 'Caption', body: 'Gemini (or a fallback line) writes the text stored here.' },
            { title: 'Query later', body: 'Intelligence Query retrieves these rows.' },
          ]}
        />
      </EmptyState>
    )
  }

  if (status?.status !== 'ready') {
    return (
      <EmptyState
        title="Captions are not written yet"
        body="This list fills at the last ingest stage. Until then there is no text for search to read."
        action={
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-sans text-xs font-semibold uppercase tracking-wider text-[#CB2957] border border-[#CB2957]/40 px-4 py-2 rounded-md">
            Watch Pipeline →
          </Link>
        }
      />
    )
  }

  if (events.length === 0) {
    return (
      <EmptyState
        title="Processing finished with an empty index"
        body="YOLO did not keep any objects (or they were too small). There is nothing to caption or retrieve."
      />
    )
  }

  return (
    <div className="px-6 py-6 font-sans">
      {/* Header */}
      <div className="mb-5 space-y-1">
        <div className="text-xs font-bold uppercase tracking-wider text-[#CB2957]">Event Index Catalog</div>
        <h1 className="text-2xl font-bold text-white">Indexed Event Catalog ({events.length})</h1>
        <p className="text-xs sm:text-sm text-[#CCCCCC] leading-relaxed max-w-2xl">
          Each entry represents a detected surveillance event. Click on any thumbnail to zoom the frame, or click "Show Details" to view full vision analysis.
        </p>
        <p className="font-mono text-xs text-[#AAAAAA] pt-0.5">
          {video.video_id} · {video.camera_id}
        </p>
      </div>

      {/* Stats bar */}
      <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="bg-[#080808] p-4 rounded-lg border border-[#222222]">
          <div className="text-xs font-bold uppercase tracking-wider text-[#AAAAAA] mb-1">Total Indexed Events</div>
          <div className="font-mono text-2xl font-bold text-white">{events.length}</div>
        </div>
        <div className="bg-[#080808] p-4 rounded-lg border border-[#222222]">
          <div className="text-xs font-bold uppercase tracking-wider text-[#AAAAAA] mb-1">Detected Classes</div>
          <div className="font-mono text-2xl font-bold text-white">
            {new Set(events.flatMap((e) => e.detected_classes)).size}
          </div>
        </div>
        <div className="bg-[#080808] p-4 rounded-lg border border-[#222222]">
          <div className="text-xs font-bold uppercase tracking-wider text-[#AAAAAA] mb-1">Avg Detection Confidence</div>
          <div className="font-mono text-2xl font-bold text-[#CB2957]">
            {Math.round((events.reduce((s, e) => s + e.confidence_score, 0) / events.length) * 100)}%
          </div>
        </div>
      </div>

      {/* Event list */}
      <div className="space-y-3">
        {events.map((event, i) => {
          const captionSource = event.caption_source
          const sceneCount = event.object_count ?? 1
          const isExpanded = expandedId === event.event_id

          return (
            <div
              key={event.event_id}
              className="group relative rounded-lg border border-[#222222] bg-[#080808] p-3.5 hover:border-[#CB2957]/40 transition-all duration-200"
            >
              <div className="flex flex-col sm:flex-row gap-4 items-start">
                {/* Index badge */}
                <div className="shrink-0 font-mono text-xs font-bold text-[#AAAAAA] bg-[#141414] px-2 py-0.5 rounded border border-[#222222]">
                  #{String(i + 1).padStart(2, '0')}
                </div>

                {/* Thumbnail */}
                <div
                  className="shrink-0 relative cursor-pointer group/thumb"
                  onClick={() => event.thumbnail_url && setZoomedUrl(event.thumbnail_url)}
                >
                  <div className="relative overflow-hidden rounded-md border border-[#222222] bg-[#000000]">
                    <AuthenticatedImage
                      path={event.thumbnail_url}
                      alt={event.caption}
                      className="h-[80px] w-[120px] object-cover"
                    />
                    <div className="absolute top-1 left-1 flex items-center gap-1 bg-black/70 px-1.5 py-0.5 rounded text-[9px] text-white">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#CB2957] animate-pulse" />
                      <span>REC</span>
                    </div>
                  </div>
                </div>

                {/* Caption & Metadata */}
                <div className="flex-1 min-w-0 space-y-1.5">
                  <div className="flex items-center justify-between flex-wrap gap-2 border-b border-[#181818] pb-1.5">
                    <div className="font-mono text-xs font-semibold text-[#EEEEEE] bg-[#111111] px-2 py-0.5 rounded border border-[#222222]">
                      ⏱ {event.start_timestamp} → {event.end_timestamp}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[#CCCCCC] font-medium">
                        {captionSourceLabel(captionSource)}
                      </span>
                      <Confidence score={event.confidence_score} />
                    </div>
                  </div>

                  <p className={`text-xs sm:text-sm text-[#DDDDDD] leading-relaxed ${isExpanded ? '' : 'line-clamp-2'}`}>
                    {event.caption}
                  </p>

                  <div className="flex items-center justify-between flex-wrap gap-2 pt-0.5">
                    <div className="flex flex-wrap gap-1.5">
                      {event.detected_classes.map((cls) => (
                        <Badge key={cls} label={cls} variant="default" />
                      ))}
                      {sceneCount > 1 && (
                        <Badge label={`objects ×${sceneCount}`} variant="default" />
                      )}
                      <Badge
                        label={captionSourceShort(captionSource)}
                        variant={captionSource === 'vlm' ? 'accent' : 'default'}
                      />
                    </div>

                    <button
                      type="button"
                      onClick={() => setExpandedId(isExpanded ? null : event.event_id)}
                      className="text-xs font-medium text-[#CB2957] hover:text-[#e0325f] transition-colors"
                    >
                      {isExpanded ? '▲ Hide Details' : '▼ Show Details'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Frame Zoom Lightbox Modal */}
      {zoomedUrl && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4 backdrop-blur-md"
          onClick={() => setZoomedUrl(null)}
        >
          <div className="relative max-w-3xl w-full bg-[#0a0a0a] rounded-lg border border-[#333333] p-4 space-y-3" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-[#222222] pb-2.5">
              <div className="text-xs sm:text-sm font-semibold text-[#EEEEEE]">CCTV Evidence Frame Inspection</div>
              <button
                type="button"
                onClick={() => setZoomedUrl(null)}
                className="text-xs font-sans text-[#CCCCCC] hover:text-white px-2.5 py-1 bg-[#1c1c1c] rounded"
              >
                ✕ Close
              </button>
            </div>
            <div className="overflow-hidden rounded-md border border-[#222222] max-h-[70vh] flex items-center justify-center bg-black">
              <AuthenticatedImage
                path={zoomedUrl}
                alt="Zoomed CCTV Event Frame"
                className="max-h-[65vh] w-auto object-contain"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
