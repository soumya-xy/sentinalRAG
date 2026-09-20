import { useState } from 'react'
import { AuthenticatedImage } from '../../components/AuthenticatedImage.tsx'
import { Confidence } from '../../components/Confidence.tsx'
import { captionSourceLabel } from '../../lib/pipelineCopy.ts'
import type { Citation } from '../../types/api.ts'

/**
 * Format raw markdown-style captions into clean structured lines/bullet points
 */
function formatCaptionText(caption: string): { summary: string; sections: Array<{ title?: string; items: string[] }> } {
  if (!caption) return { summary: 'No caption details available.', sections: [] }

  // Clean raw asterisks and markdown symbols for preview
  const cleanSummary = caption
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/\d+\.\s+/g, '')
    .trim()

  // First line or short preview
  const preview = cleanSummary.length > 130 ? cleanSummary.slice(0, 130) + '…' : cleanSummary

  // Split caption by sections or numbered lists
  const parts = caption.split(/(?=\d+\.\s+\*\*|\*\*)/g).filter(Boolean)

  const sections: Array<{ title?: string; items: string[] }> = []

  for (const part of parts) {
    const trimmed = part.trim()
    if (!trimmed) continue

    const titleMatch = trimmed.match(/^(?:\d+\.\s*)?\*\*([^*]+)\*\*:?(.*)/s)
    if (titleMatch) {
      const title = titleMatch[1].replace(/:$/, '').trim()
      const content = titleMatch[2].trim()

      const items = content
        .split(/\s*\*\s+/)
        .map((s) => s.replace(/\*\*/g, '').trim())
        .filter(Boolean)

      sections.push({ title, items: items.length > 0 ? items : [content.replace(/\*\*/g, '').trim()] })
    } else {
      const items = trimmed
        .split(/\s*\*\s+/)
        .map((s) => s.replace(/\*\*/g, '').trim())
        .filter(Boolean)

      sections.push({ items })
    }
  }

  return { summary: preview, sections }
}

export function CitationCard({ citation }: { citation: Citation }) {
  const [expanded, setExpanded] = useState(false)
  const [zoomed, setZoomed] = useState(false)
  const hasThumb = Boolean(citation.thumbnail_url)
  const { summary, sections } = formatCaptionText(citation.caption)

  return (
    <article className="group relative rounded-lg border border-[#222222] bg-[#080808] p-3.5 hover:border-[#CB2957]/40 transition-all duration-200 font-sans">
      {/* Accent left border indicator */}
      <div className="absolute left-0 top-0 h-full w-1 rounded-l-lg bg-gradient-to-b from-[#CB2957] to-transparent opacity-40 group-hover:opacity-100 transition-opacity" />

      <div className="flex flex-col sm:flex-row gap-3.5 items-start">
        {/* Thumbnail preview with REC badge */}
        <div className="shrink-0 relative group/thumb cursor-pointer" onClick={() => setZoomed(!zoomed)}>
          <div className="relative overflow-hidden rounded-md border border-[#222222] bg-[#000000]">
            <AuthenticatedImage
              path={citation.thumbnail_url}
              alt={`CCTV Frame at ${citation.start_timestamp}`}
              className="h-[84px] w-[126px] object-cover"
            />
            {/* REC badge */}
            <div className="absolute top-1.5 left-1.5 flex items-center gap-1 bg-black/70 backdrop-blur-sm px-1.5 py-0.5 rounded text-[9px] font-sans font-medium text-white border border-white/10">
              <span className="h-1.5 w-1.5 rounded-full bg-[#CB2957] animate-pulse" />
              <span>REC</span>
            </div>
            {/* Click to zoom overlay */}
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/thumb:opacity-100 transition-opacity flex items-center justify-center text-[11px] font-sans text-white font-medium">
              Zoom Frame
            </div>
          </div>
        </div>

        {/* Metadata and content */}
        <div className="flex-1 min-w-0 space-y-1.5">
          {/* Header row: Timestamps & Confidence */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#181818] pb-1.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold text-[#EEEEEE] bg-[#141414] px-2 py-0.5 rounded border border-[#262626]">
                ⏱ {citation.start_timestamp} → {citation.end_timestamp}
              </span>
              <span className="text-[11px] font-sans text-[#CCCCCC] bg-[#111111] px-2 py-0.5 rounded border border-[#222222]">
                📹 {citation.camera_id}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[11px] font-sans text-[#AAAAAA]">
                {captionSourceLabel(citation.caption_source)}
              </span>
              <Confidence score={citation.confidence_score} />
            </div>
          </div>

          {/* Collapsed vs Expanded Text Display */}
          {!expanded ? (
            <div className="pt-0.5">
              <p className="text-xs sm:text-sm font-sans text-[#DDDDDD] leading-relaxed">
                {summary}
              </p>
            </div>
          ) : (
            <div className="pt-1 space-y-2.5">
              {sections.map((sec, idx) => (
                <div key={idx} className="bg-[#0f0f0f] p-2.5 rounded-md border border-[#1f1f1f] space-y-1">
                  {sec.title && (
                    <h5 className="text-[11px] font-sans font-bold uppercase tracking-wider text-[#CB2957]">
                      {sec.title}
                    </h5>
                  )}
                  <ul className="space-y-1">
                    {sec.items.map((item, itemIdx) => (
                      <li key={itemIdx} className="text-xs sm:text-sm font-sans text-[#EEEEEE] leading-relaxed flex items-start gap-1.5">
                        <span className="text-[#CB2957] font-bold mt-0.5">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}

          {/* Expand / Collapse Toggle Button */}
          <div className="pt-1 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="inline-flex items-center gap-1 text-xs font-sans font-medium text-[#CB2957] hover:text-[#e0325f] transition-colors py-0.5 px-2 rounded bg-[#CB2957]/10 hover:bg-[#CB2957]/20 border border-[#CB2957]/30"
            >
              <span>{expanded ? '▲ Hide Full Evidence Breakdown' : '▼ Show Full Evidence Breakdown'}</span>
            </button>
            <span className="font-mono text-[10px] text-[#888888]">
              {citation.event_id}
            </span>
          </div>
        </div>
      </div>

      {/* Frame Zoom Lightbox Modal */}
      {zoomed && hasThumb && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4 backdrop-blur-md"
          onClick={() => setZoomed(false)}
        >
          <div className="relative max-w-3xl w-full bg-[#0a0a0a] rounded-lg border border-[#333333] p-4 space-y-3" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-[#222222] pb-2.5">
              <div className="font-sans text-xs sm:text-sm font-semibold text-[#EEEEEE]">
                CCTV Evidence Frame — {citation.camera_id} ({citation.start_timestamp} → {citation.end_timestamp})
              </div>
              <button
                type="button"
                onClick={() => setZoomed(false)}
                className="text-xs font-sans text-[#CCCCCC] hover:text-white px-2 py-1 bg-[#1c1c1c] rounded"
              >
                ✕ Close
              </button>
            </div>
            <div className="overflow-hidden rounded-md border border-[#222222] max-h-[70vh] flex items-center justify-center bg-black">
              <AuthenticatedImage
                path={citation.thumbnail_url}
                alt={`CCTV Frame at ${citation.start_timestamp}`}
                className="max-h-[65vh] w-auto object-contain"
              />
            </div>
          </div>
        </div>
      )}
    </article>
  )
}
