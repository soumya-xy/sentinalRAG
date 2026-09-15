import { Confidence } from '../../components/Confidence.tsx'
import { resolveMediaUrl } from '../../lib/api/client.ts'
import type { Citation } from '../../types/api.ts'

export function CitationCard({ citation }: { citation: Citation }) {
  const src = resolveMediaUrl(citation.thumbnail_url)

  return (
    <article className="grid grid-cols-[10rem_1fr] gap-4 border border-border bg-surface p-3">
      {src ? (
        <img
          src={src}
          alt={`Frame at ${citation.start_timestamp}`}
          className="h-[90px] w-full border border-border object-cover"
        />
      ) : (
        <div className="flex h-[90px] items-center justify-center border border-border bg-base font-mono text-xs text-muted">
          no frame
        </div>
      )}
      <div className="min-w-0">
        <div className="font-mono text-sm">
          {citation.start_timestamp}–{citation.end_timestamp}
        </div>
        <div className="mt-1 font-mono text-xs text-muted">
          {citation.camera_id}  {citation.video_id}  {citation.event_id}
        </div>
        <div className="mt-1">
          <Confidence score={citation.confidence_score} />
        </div>
        <p className="mt-2 max-w-prose text-sm text-muted">{citation.caption}</p>
      </div>
    </article>
  )
}
