import { useState, useRef, useEffect, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '../../components/Button.tsx'
import { EmptyState } from '../../components/EmptyState.tsx'
import { ErrorBanner } from '../../components/ErrorBanner.tsx'
import { ProcessTrail } from '../../components/ProcessTrail.tsx'
import { ProvenanceNote } from '../../components/ProvenanceNote.tsx'
import { TextArea } from '../../components/Input.tsx'
import { api, ApiError } from '../../lib/api/index.ts'
import { answerSourceLabel, currentStageHeadline } from '../../lib/pipelineCopy.ts'
import type { QueryResponse, VideoRecord, VideoStatusResponse } from '../../types/api.ts'
import { CitationCard } from './CitationCard.tsx'

const SAMPLE_QUESTIONS = [
  'Did anyone in a red jacket appear in the footage?',
  'How many people were visible near the entrance?',
  'Was a vehicle present at any point?',
  'Was a bag left unattended?',
  'What signage or text was visible in the scene?',
]

interface Turn {
  id: string
  question: string
  response: QueryResponse | null
  error: string | null
  pending: boolean
}

export function ConversationTab({
  video,
  status,
}: {
  video: VideoRecord | null
  status: VideoStatusResponse | null
}) {
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const isReady = Boolean(video && status?.status === 'ready')
  const isProcessing = status?.status === 'processing' || status?.status === 'uploaded'

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns.length])

  async function submit(text: string) {
    const trimmed = text.trim()
    if (!video || !trimmed || submitting || !isReady) return
    setSubmitError(null)
    setSubmitting(true)
    setQuestion('')

    const id = crypto.randomUUID()
    setTurns((prev) => [...prev, { id, question: trimmed, response: null, error: null, pending: true }])

    try {
      const response = await api.query({ question: trimmed, video_id: video.video_id })
      setTurns((prev) => prev.map((t) => t.id === id ? { ...t, response, pending: false } : t))
    } catch (err) {
      const message = err instanceof ApiError ? err.detail : 'Query failed'
      setTurns((prev) => prev.map((t) => t.id === id ? { ...t, error: message, pending: false } : t))
      setSubmitError(message)
    } finally {
      setSubmitting(false)
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void submit(question)
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void submit(question)
    }
  }

  /* ── Empty States ────────────────────────────────────────── */
  if (!video) {
    return (
      <EmptyState
        title="Nothing to ask yet"
        body="Questions search an index of captions, not the raw video. Upload footage first so YOLO, Gemini, and pgvector can build that index."
        action={
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-sans text-xs font-semibold uppercase tracking-wider text-[#CB2957] hover:text-[#e0325f] border border-[#CB2957]/40 px-4 py-2 rounded-md transition-all">
            Ingest Footage →
          </Link>
        }
      >
        <ProcessTrail
          steps={[
            { title: 'Upload a clip', body: 'The file is stored securely in Supabase Storage.' },
            { title: 'Index is built', body: 'YOLO finds objects, Gemini writes captions, vectors are embedded.' },
            { title: 'Then you ask', body: 'Answers are composed from retrieved captions and candidate frames.' },
          ]}
        />
      </EmptyState>
    )
  }

  if (isProcessing) {
    return (
      <EmptyState
        title="Index is still being written"
        body={currentStageHeadline(status?.stages, status?.current_stage, status?.status)}
        action={
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-sans text-xs font-semibold uppercase tracking-wider text-[#CB2957] hover:text-[#e0325f] border border-[#CB2957]/40 px-4 py-2 rounded-md transition-all">
            Watch Pipeline →
          </Link>
        }
      >
        <ProcessTrail
          steps={[
            { title: 'Now', body: 'Frames are being turned into events and captions.' },
            { title: 'Next', body: 'When status is ready, those captions become searchable.' },
          ]}
        />
      </EmptyState>
    )
  }

  if (status?.status === 'failed') {
    return (
      <EmptyState
        title="No index to query"
        body={status.error ?? 'Ingest stopped before captions were written. Retry from Ingest Footage.'}
        action={
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-sans text-xs font-semibold uppercase tracking-wider text-[#CB2957] border border-[#CB2957]/40 px-4 py-2 rounded-md">
            Retry on Ingest
          </Link>
        }
      />
    )
  }

  /* ── Main Chat UI ────────────────────────────────────────── */
  return (
    <div className="flex h-full flex-col font-sans">

      {/* Feed metadata banner */}
      <div className="border-b border-[#1f1f1f] bg-[#050505] px-6 py-2.5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-[#22c55e]/10 border border-[#22c55e]/20 px-2.5 py-0.5 rounded-full">
            <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e] animate-pulse" />
            <span className="text-[11px] font-semibold text-[#22c55e] uppercase tracking-wider">Index Ready</span>
          </div>
          <span className="text-xs font-medium text-[#DDDDDD]">
            📹 {video.camera_id} <span className="text-[#AAAAAA]">({video.original_filename})</span>
          </span>
        </div>
        {status?.caption_mode && (
          <span className="text-[11px] font-medium text-[#CCCCCC] bg-[#111111] px-2.5 py-0.5 rounded border border-[#222222]">
            Captions: {status.caption_mode === 'vlm' ? 'Gemini 2.5 Vision' : 'Rule-based'}
          </span>
        )}
      </div>

      <div className="border-b border-[#181818] bg-[#080808] px-6 py-2 shrink-0">
        <p className="text-xs text-[#CCCCCC] leading-relaxed">
          Questions are matched against indexed event captions, then answered with visual evidence citations.
        </p>
      </div>

      {/* Conversation scroll area */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
        {turns.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center py-10">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-[#222222] bg-[#0c0c0c]">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-[#CB2957]">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5"/>
                <path d="M12 7v5l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <h3 className="text-base font-semibold text-[#EEEEEE] mb-1">Ready to query surveillance footage</h3>
            <p className="text-xs text-[#CCCCCC] max-w-md leading-relaxed">
              Ask about people, clothing, vehicles, objects, or timestamps. Responses pull directly from stored events.
            </p>
            <ProcessTrail
              steps={[
                { title: 'Retrieve', body: 'Question is matched to stored caption vector embeddings.' },
                { title: 'Inspect & Compose', body: 'Gemini visually inspects candidate frames to compose an accurate answer.' },
                { title: 'Cite', body: 'Every response links directly to timestamped CCTV evidence frames.' },
              ]}
            />
          </div>
        ) : (
          turns.map((turn) => (
            <article key={turn.id} className="reveal space-y-4">
              {/* Question */}
              <div className="flex items-start gap-3">
                <div className="shrink-0 flex h-7 w-7 items-center justify-center rounded-full bg-[#181818] border border-[#2c2c2c] text-xs text-[#DDDDDD] font-semibold">
                  👤
                </div>
                <div className="flex-1">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-[#AAAAAA] mb-1">Operator Query</div>
                  <p className="text-sm text-[#EEEEEE] font-medium bg-[#0a0a0a] p-3 rounded-lg border border-[#222222] inline-block">{turn.question}</p>
                </div>
              </div>

              {/* Answer */}
              {turn.pending ? (
                <div className="ml-10 space-y-2.5">
                  <div className="flex items-center gap-2 py-1.5">
                    <span className="h-2 w-2 rounded-full bg-[#CB2957] animate-ping" />
                    <span className="text-xs font-semibold text-[#DDDDDD] uppercase tracking-wider">Searching Vector Index & Inspecting Frames…</span>
                  </div>
                </div>
              ) : turn.response ? (
                <div className="ml-10 space-y-4 reveal">
                  <ProvenanceNote label="Answer Source Provenance">
                    {turn.response.provenance
                      ?? 'Retrieved matching event captions, inspected image frames, and composed grounded answer.'}
                  </ProvenanceNote>
                  <div className="bg-[#080808] p-4 rounded-lg border border-[#222222] space-y-2">
                    <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-1.5">
                      <div className="text-xs font-bold uppercase tracking-wider text-[#CB2957] flex items-center gap-1.5">
                        <span>🎯</span>
                        <span>{answerSourceLabel(turn.response.answer_source)}</span>
                      </div>
                    </div>
                    <p className="text-sm text-[#EEEEEE] leading-relaxed">
                      {turn.response.answer}
                    </p>
                  </div>

                  {turn.response.citations.length > 0 ? (
                    <div className="space-y-2.5">
                      <div className="flex items-center justify-between">
                        <div className="text-xs font-bold uppercase tracking-wider text-[#CCCCCC] flex items-center gap-1.5">
                          <span>📸</span>
                          <span>Visual Evidence Citations ({turn.response.citations.length})</span>
                        </div>
                        <span className="text-[11px] text-[#AAAAAA]">Click thumbnail to zoom image</span>
                      </div>
                      <div className="space-y-2.5">
                        {turn.response.citations.map((citation) => (
                          <CitationCard key={citation.event_id} citation={citation} />
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-[#AAAAAA] italic">
                      No events matched the search criteria with high confidence.
                    </p>
                  )}
                </div>
              ) : turn.error ? (
                <div className="ml-10">
                  <ErrorBanner message={turn.error} />
                </div>
              ) : null}

              {/* Divider */}
              <div className="border-b border-[#181818]" />
            </article>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-[#1f1f1f] bg-[#050505] px-6 py-4 shrink-0 space-y-2.5">
        {submitError && turns.length === 0 ? (
          <div className="mb-2 max-w-2xl">
            <ErrorBanner message={submitError} />
          </div>
        ) : null}

        <form onSubmit={onSubmit} className="flex flex-col gap-2.5">
          <TextArea
            id="query-input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask anything about the footage (e.g., 'Did anyone in a red jacket appear?'). Press Enter to submit."
            disabled={!isReady || submitting}
            rows={2}
            className="text-sm p-3 bg-[#0a0a0a] border-[#2b2b2b] rounded-lg text-[#EEEEEE] focus:border-[#CB2957]"
          />
          <div className="flex items-center justify-between flex-wrap gap-2.5">
            <div className="flex flex-wrap gap-1.5">
              <span className="text-xs text-[#AAAAAA] font-medium flex items-center">Suggested:</span>
              {SAMPLE_QUESTIONS.slice(0, 3).map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => void submit(q)}
                  disabled={!isReady || submitting}
                  className="text-xs font-medium text-[#DDDDDD] hover:text-[#CB2957] bg-[#111111] hover:bg-[#181818] border border-[#222222] hover:border-[#CB2957]/40 px-2.5 py-1 rounded transition-all disabled:opacity-40"
                >
                  {q}
                </button>
              ))}
            </div>
            <Button
              type="submit"
              disabled={!isReady || submitting || !question.trim()}
              size="md"
              className="px-5 font-semibold text-xs"
            >
              {submitting ? 'Querying Index…' : 'Search Footage'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
