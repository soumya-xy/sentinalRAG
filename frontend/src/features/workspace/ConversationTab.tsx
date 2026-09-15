import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '../../components/Button.tsx'
import { EmptyState } from '../../components/EmptyState.tsx'
import { ErrorBanner } from '../../components/ErrorBanner.tsx'
import { TextArea } from '../../components/Input.tsx'
import { api, ApiError } from '../../lib/api/index.ts'
import type { QueryResponse, VideoRecord, VideoStatusResponse } from '../../types/api.ts'
import { CitationCard } from './CitationCard.tsx'

const SAMPLES = [
  'Did anyone in a red jacket enter after 21:00?',
  'How many people appeared in the lobby?',
  'Was a vehicle present near the entrance?',
  'Was a bag left unattended?',
]

interface Turn {
  question: string
  response: QueryResponse | null
  error: string | null
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
  const [pending, setPending] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const ready = Boolean(video && status?.status === 'ready')
  const processing = status?.status === 'processing' || status?.status === 'uploaded'

  async function submit(text: string) {
    const trimmed = text.trim()
    if (!video || !trimmed || pending) return
    setSubmitError(null)
    setPending(true)
    setQuestion('')
    const placeholder: Turn = { question: trimmed, response: null, error: null }
    setTurns((current) => [...current, placeholder])
    try {
      await new Promise((resolve) => window.setTimeout(resolve, 420))
      const response = await api.query({ question: trimmed, video_id: video.video_id })
      setTurns((current) => {
        const next = [...current]
        next[next.length - 1] = { question: trimmed, response, error: null }
        return next
      })
    } catch (error) {
      const message = error instanceof ApiError ? error.detail : 'Query failed'
      setTurns((current) => {
        const next = [...current]
        next[next.length - 1] = { question: trimmed, response: null, error: message }
        return next
      })
      setSubmitError(message)
    } finally {
      setPending(false)
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    void submit(question)
  }

  if (!video) {
    return (
      <EmptyState
        title="No footage indexed"
        body="Upload a recorded video first. The conversation is available after the batch pipeline finishes."
        action={
          <Link to="/workspace?tab=video" className="text-sm text-sage hover:text-ink">
            Open ingest
          </Link>
        }
      />
    )
  }

  if (processing) {
    return (
      <EmptyState
        title="Index not ready"
        body="Batch processing is still running. Questions are answered from the event index, which is written at the last stage."
        action={
          <Link to="/workspace?tab=video" className="text-sm text-sage hover:text-ink">
            Watch processing
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
          <Link to="/workspace?tab=video" className="text-sm text-sage hover:text-ink">
            Return to ingest
          </Link>
        }
      />
    )
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-medium">Ask the indexed footage</h1>
      <p className="mt-2 max-w-prose text-sm text-muted">
        Answers are retrieved from event captions and returned with a timestamp, camera, and
        cited frame.
      </p>

      {turns.length === 0 ? (
        <p className="mt-8 text-sm text-muted">No questions yet in this session.</p>
      ) : (
        <div className="mt-8 space-y-8">
          {turns.map((turn, index) => (
            <article key={`${turn.question}-${index}`} className="border-t border-border pt-6">
              <div className="text-sm text-muted">Question</div>
              <p className="mt-1">{turn.question}</p>
              {turn.response ? (
                <div className="reveal mt-5">
                  <div className="text-sm text-muted">Answer</div>
                  <p className="mt-1 max-w-prose">{turn.response.answer}</p>
                  <div className="mt-4 space-y-3">
                    {turn.response.citations.map((citation) => (
                      <CitationCard key={citation.event_id} citation={citation} />
                    ))}
                  </div>
                </div>
              ) : turn.error ? (
                <div className="mt-4">
                  <ErrorBanner message={turn.error} />
                </div>
              ) : (
                <p className="mt-5 font-mono text-sm text-muted">Retrieving events…</p>
              )}
            </article>
          ))}
        </div>
      )}

      <form onSubmit={onSubmit} className="mt-10">
        {submitError && turns.length === 0 ? <ErrorBanner message={submitError} /> : null}
        <TextArea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about people, objects, clothing, or a time window"
          disabled={!ready || pending}
        />
        <div className="mt-3 flex items-center gap-4">
          <Button type="submit" disabled={!ready || pending || question.trim().length < 3}>
            {pending ? 'Asking…' : 'Ask'}
          </Button>
          <span className="font-mono text-xs text-muted">
            {video.camera_id}  {video.video_id}
          </span>
        </div>
      </form>

      <div className="mt-8">
        <div className="mb-2 text-sm text-muted">Sample questions</div>
        <div className="space-y-1">
          {SAMPLES.map((sample) => (
            <button
              key={sample}
              type="button"
              className="block text-left text-sm text-muted hover:text-ink"
              onClick={() => void submit(sample)}
              disabled={!ready || pending}
            >
              {sample}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
