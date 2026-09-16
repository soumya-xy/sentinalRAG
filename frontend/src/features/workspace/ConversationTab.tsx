import { useState, useRef, useEffect, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '../../components/Button.tsx'
import { EmptyState } from '../../components/EmptyState.tsx'
import { ErrorBanner } from '../../components/ErrorBanner.tsx'
import { TextArea } from '../../components/Input.tsx'
import { api, ApiError } from '../../lib/api/index.ts'
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
        title="No footage indexed"
        body="Upload a recorded CCTV video first. The intelligence query interface activates after the full pipeline completes."
        action={
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#CB2957] hover:text-[#e0325f] border border-[#CB2957]/40 px-4 py-2 rounded-sm transition-all">
            Ingest Footage →
          </Link>
        }
      />
    )
  }

  if (isProcessing) {
    return (
      <EmptyState
        title="Index not ready"
        body="Batch processing is still running. The query interface unlocks after the pgvector index stage completes."
        action={
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#CB2957] hover:text-[#e0325f] border border-[#CB2957]/40 px-4 py-2 rounded-sm transition-all">
            Watch Pipeline →
          </Link>
        }
      />
    )
  }

  if (status?.status === 'failed') {
    return (
      <EmptyState
        title="Processing failed"
        body={status.error ?? 'This video did not finish indexing. Re-upload to try again.'}
        action={
          <Link to="/workspace?tab=video" className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#CB2957] border border-[#CB2957]/40 px-4 py-2 rounded-sm">
            Return to Ingest
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
            Caption: {status.caption_mode}
          </span>
        )}
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
            <p className="font-mono text-xs uppercase tracking-widest text-[#777777] mb-2">Intelligence Query Ready</p>
            <p className="text-xs text-[#888888] max-w-sm">
              Ask any question about the indexed footage. Answers are grounded to timestamp evidence and visual citations.
            </p>
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
                <div className="flex items-start gap-3 ml-9">
                  <div className="flex items-center gap-2 py-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#CB2957] pulse-dot" />
                    <span className="font-mono text-xs text-[#999999] uppercase tracking-widest">Querying index…</span>
                  </div>
                </div>
              ) : turn.response ? (
                <div className="ml-9 space-y-4 reveal">
                  <div>
                    <div className="font-mono text-[9px] uppercase tracking-widest text-[#CB2957] mb-2">Intelligence Response</div>
                    <p className="text-sm text-[#DDDDDD] leading-relaxed border-l-2 border-[#CB2957]/30 pl-4">
                      {turn.response.answer}
                    </p>
                  </div>
                  {turn.response.citations.length > 0 && (
                    <div>
                      <div className="font-mono text-[9px] uppercase tracking-widest text-[#888888] mb-3">
                        Visual Evidence ({turn.response.citations.length})
                      </div>
                      <div className="space-y-3">
                        {turn.response.citations.map((citation) => (
                          <CitationCard key={citation.event_id} citation={citation} />
                        ))}
                      </div>
                    </div>
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
            placeholder="Ask about people, clothing, vehicles, objects, or time windows…"
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
              {submitting ? 'Querying…' : 'Query Index'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
