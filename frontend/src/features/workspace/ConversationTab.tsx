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
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#CB2957] hover:text-[#e0325f] border border-[#CB2957]/40 px-4 py-2 rounded-sm transition-all">
            Ingest Footage →
          </Link>
        }
      >
        <ProcessTrail
          steps={[
            { title: 'Upload a clip', body: 'The file is stored in Supabase. Nothing user-specific stays on this machine.' },
            { title: 'Index is built', body: 'YOLO finds objects, Gemini writes captions, those sentences are embedded.' },
            { title: 'Then you ask', body: 'The answer is composed only from retrieved captions and their frames.' },
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
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#CB2957] hover:text-[#e0325f] border border-[#CB2957]/40 px-4 py-2 rounded-sm transition-all">
            Watch Pipeline →
          </Link>
        }
      >
        <ProcessTrail
          steps={[
            { title: 'Now', body: 'Frames are being turned into events and captions. That text is not on this screen yet.' },
            { title: 'Next', body: 'When status is ready, those captions become the only source for answers.' },
          ]}
        />
      </EmptyState>
    )
  }

  if (status?.status === 'failed') {
    return (
      <EmptyState
        title="No index to query"
        body={status.error ?? 'Ingest stopped before captions were written. Retry the same file from Ingest Footage — there is nothing here to search.'}
        action={
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#CB2957] border border-[#CB2957]/40 px-4 py-2 rounded-sm">
            Retry on Ingest
          </Link>
        }
      />
    )
  }

  /* ── Main Chat UI ────────────────────────────────────────── */
  return (
    <div className="flex h-full flex-col">

      {/* Feed metadata banner */}
      <div className="border-b border-[#111111] bg-[#030303] px-8 py-3 flex items-center gap-6 shrink-0">
        <div className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e] pulse-dot" />
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#22c55e]">Index Ready</span>
        </div>
        <span className="font-mono text-[10px] text-[#777777] uppercase tracking-widest">
          {video.camera_id} · {video.video_id}
        </span>
        {status?.caption_mode && (
          <span className="font-mono text-[10px] text-[#777777] uppercase tracking-widest">
            Captions: {status.caption_mode === 'vlm' ? 'Gemini vision' : 'rule-based'}
          </span>
        )}
      </div>
      <div className="border-b border-[#111111] bg-[#050505] px-8 py-2.5 shrink-0">
        <p className="text-xs text-[#888888] leading-relaxed">
          A question is embedded, matched against this video’s event captions, then answered only from those hits.
          The paragraph you see is not a free-form watch of the file.
        </p>
      </div>

      {/* Conversation scroll area */}
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        {turns.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center py-12">
            <div className="mb-6 h-12 w-12 rounded-sm border border-[#1a1a1a] bg-[#050505] flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#CB2957]">
                <circle cx="10" cy="10" r="8.5" stroke="currentColor" strokeWidth="1.2"/>
                <path d="M10 6v5l3 2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
            </div>
            <p className="font-mono text-xs uppercase tracking-widest text-[#777777] mb-2">Ready to search the index</p>
            <p className="text-xs text-[#888888] max-w-md leading-relaxed">
              Type a question about people, clothing, vehicles, or time. The system will retrieve stored events first.
              The answer appears only after that retrieval — and the frames under it are the events it used.
            </p>
            <ProcessTrail
              steps={[
                { title: 'Retrieve', body: 'Your question is compared to caption embeddings for this video only.' },
                { title: 'Compose', body: 'Gemini writes a short answer from those captions and frames.' },
                { title: 'Cite', body: 'Each card below the answer is an indexed event, not a new image generation.' },
              ]}
            />
          </div>
        ) : (
          turns.map((turn) => (
            <article key={turn.id} className="reveal space-y-4">
              {/* Question */}
              <div className="flex items-start gap-3">
                <div className="shrink-0 flex h-6 w-6 items-center justify-center rounded-sm bg-[#1a1a1a] border border-[#222222]">
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none" className="text-[#AAAAAA]">
                    <circle cx="5" cy="3.5" r="1.8" stroke="currentColor" strokeWidth="0.9"/>
                    <path d="M1 9c0-2.2 1.8-3.5 4-3.5s4 1.3 4 3.5" stroke="currentColor" strokeWidth="0.9"/>
                  </svg>
                </div>
                <div className="flex-1">
                  <div className="font-mono text-[9px] uppercase tracking-widest text-[#888888] mb-1">Operator Query</div>
                  <p className="text-sm text-[#DDDDDD]">{turn.question}</p>
                </div>
              </div>

              {/* Answer */}
              {turn.pending ? (
                <div className="ml-9 space-y-3">
                  <div className="flex items-center gap-2 py-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#CB2957] pulse-dot" />
                    <span className="font-mono text-xs text-[#999999] uppercase tracking-widest">Working through the index</span>
                  </div>
                  <ProcessTrail
                    steps={[
                      { title: 'Embed question', body: 'Same embedding model as the stored captions.' },
                      { title: 'Retrieve events', body: 'Only this video. Weak matches are dropped.' },
                      { title: 'Compose + cite', body: 'Answer text is written after retrieval, then attached to those events.' },
                    ]}
                  />
                </div>
              ) : turn.response ? (
                <div className="ml-9 space-y-4 reveal">
                  <ProvenanceNote label="Where this answer came from">
                    {turn.response.provenance
                      ?? 'Retrieved indexed events for this video, then composed the answer from those rows.'}
                  </ProvenanceNote>
                  <div>
                    <div className="font-mono text-[9px] uppercase tracking-widest text-[#CB2957] mb-2">
                      {answerSourceLabel(turn.response.answer_source)}
                    </div>
                    <p className="text-sm text-[#DDDDDD] leading-relaxed border-l-2 border-[#CB2957]/30 pl-4">
                      {turn.response.answer}
                    </p>
                  </div>
                  {turn.response.citations.length > 0 ? (
                    <div>
                      <div className="font-mono text-[9px] uppercase tracking-widest text-[#888888] mb-1">
                        Evidence from the index ({turn.response.citations.length})
                      </div>
                      <p className="text-xs text-[#777777] mb-3">
                        These frames and captions already existed from ingest. They are the events the answer used.
                      </p>
                      <div className="space-y-3">
                        {turn.response.citations.map((citation) => (
                          <CitationCard key={citation.event_id} citation={citation} />
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-[#777777]">
                      No event passed the retrieval floor, so there is no thumbnail to show — the system did not invent one.
                    </p>
                  )}
                </div>
              ) : turn.error ? (
                <div className="ml-9">
                  <ErrorBanner message={turn.error} />
                </div>
              ) : null}

              {/* Divider */}
              <div className="border-b border-[#111111]" />
            </article>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-[#1a1a1a] bg-[#050505] px-8 py-5 shrink-0">
        {submitError && turns.length === 0 ? (
          <div className="mb-4 max-w-2xl">
            <ErrorBanner message={submitError} />
          </div>
        ) : null}

        <form onSubmit={onSubmit} className="flex flex-col gap-3">
          <TextArea
            id="query-input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask about people, clothing, vehicles, or a time window in this clip…"
            disabled={!isReady || submitting}
            rows={3}
          />
          <div className="flex items-center justify-between">
            <div className="flex flex-wrap gap-2">
              {SAMPLE_QUESTIONS.slice(0, 3).map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => void submit(q)}
                  disabled={!isReady || submitting}
                  className="font-mono text-[10px] uppercase tracking-wide text-[#888888] hover:text-[#CB2957] border border-[#1a1a1a] hover:border-[#CB2957]/40 px-2.5 py-1 rounded-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {q.length > 36 ? q.slice(0, 36) + '…' : q}
                </button>
              ))}
            </div>
            <Button
              type="submit"
              disabled={!isReady || submitting || question.trim().length < 3}
              className="shrink-0"
            >
              {submitting ? 'Searching index…' : 'Search index'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
