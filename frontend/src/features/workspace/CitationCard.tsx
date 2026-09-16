import { Confidence } from '../../components/Confidence.tsx'
import { resolveMediaUrl } from '../../lib/api/client.ts'
import type { Citation } from '../../types/api.ts'

export function CitationCard({ citation }: { citation: Citation }) {
  const src = resolveMediaUrl(citation.thumbnail_url)

  return (
    <article className="group relative flex gap-4 rounded-sm border border-[#1a1a1a] bg-[#050505] p-3 hover:border-[#CB2957]/30 transition-all duration-200">
      {/* Accent line */}
      <div className="absolute left-0 top-0 h-full w-0.5 rounded-l-sm bg-gradient-to-b from-[#CB2957] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      {/* Thumbnail */}
      <div className="shrink-0 relative overflow-hidden rounded-sm">
        {src ? (
          <img
            src={src}
            alt={`Frame at ${citation.start_timestamp}`}
            className="h-[80px] w-[120px] object-cover border border-[#222222]"
          />
        ) : (
          <div className="flex h-[80px] w-[120px] items-center justify-center border border-[#1a1a1a] bg-[#0a0a0a]">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#777777]">
              <rect x="2" y="5" width="11" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.2"/>
              <path d="M13 8l5.5-3v10L13 12" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
            </svg>
          </div>
        )}
        {/* REC overlay */}
        <div className="absolute top-1.5 left-1.5 flex items-center gap-1">
          <span className="h-1 w-1 rounded-full bg-[#CB2957]" />
          <span className="font-mono text-[7px] text-[#CB2957] uppercase tracking-widest">REC</span>
        </div>
      </div>

      {/* Metadata */}
      <div className="flex-1 min-w-0 space-y-1.5">
        {/* Timestamp */}
        <div className="font-mono text-sm text-[#DDDDDD] tabular-nums">
          {citation.start_timestamp}
          <span className="text-[#888888] mx-1">→</span>
          {citation.end_timestamp}
        </div>

        {/* IDs */}
        <div className="font-mono text-[10px] text-[#888888] space-x-3">
          <span className="text-[#999999]">{citation.camera_id}</span>
          <span>{citation.video_id}</span>
          <span>{citation.event_id}</span>
        </div>

        {/* Confidence */}
        <div className="flex items-center gap-2">
          <span className="font-mono text-[9px] uppercase tracking-widest text-[#777777]">Confidence</span>
          <Confidence score={citation.confidence_score} />
        </div>

        {/* Caption */}
        <p className="text-xs text-[#AAAAAA] leading-relaxed line-clamp-2">{citation.caption}</p>
      </div>
    </article>
  )
}
