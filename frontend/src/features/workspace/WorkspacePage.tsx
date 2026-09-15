import { Navigate, useSearchParams } from 'react-router-dom'

import { ErrorBanner } from '../../components/ErrorBanner.tsx'
import { StatusDot } from '../../components/StatusDot.tsx'
import { useAuth } from '../../lib/auth.tsx'
import { ConversationTab } from './ConversationTab.tsx'
import { EventsTab } from './EventsTab.tsx'
import { useActiveVideo } from './useActiveVideo.ts'
import { VideoTab } from './VideoTab.tsx'

type Tab = 'conversation' | 'video' | 'events'

function asTab(value: string | null): Tab {
  if (value === 'video' || value === 'events' || value === 'conversation') return value
  return 'conversation'
}

function videoTone(
  status: string | undefined,
): 'sage' | 'warning' | 'critical' | 'muted' {
  if (status === 'ready') return 'sage'
  if (status === 'processing' || status === 'uploaded') return 'warning'
  if (status === 'failed') return 'critical'
  return 'muted'
}

export function WorkspacePage() {
  const { user, ready, logout } = useAuth()
  const [params, setParams] = useSearchParams()
  const tab = asTab(params.get('tab'))
  const { video, status, events, error, loading, adopt } = useActiveVideo()

  if (ready && !user) {
    return <Navigate to="/auth?mode=login" replace />
  }

  function go(next: Tab) {
    setParams(next === 'conversation' ? {} : { tab: next })
  }

  const navItem = (id: Tab, label: string) => {
    const active = tab === id
    return (
      <button
        type="button"
        onClick={() => go(id)}
        className={`block w-full border-l px-4 py-2 text-left text-sm ${
          active ? 'border-sage bg-surface text-ink' : 'border-transparent text-muted hover:text-ink'
        }`}
      >
        {label}
      </button>
    )
  }

  return (
    <div className="flex min-h-screen bg-base text-ink">
      <aside className="flex w-56 shrink-0 flex-col border-r border-border">
        <div className="border-b border-border px-4 py-4">
          <div className="font-semibold">SentinelRAG</div>
          <div className="text-xs text-muted">Phase 1 console</div>
        </div>
        <nav className="py-2">
          {navItem('conversation', 'Conversation')}
          {navItem('video', 'Video')}
          {navItem('events', events.length ? `Events (${events.length})` : 'Events')}
        </nav>
        <div className="mt-auto border-t border-border px-4 py-4 text-sm">
          <div className="text-muted">
            <StatusDot
              tone={videoTone(status?.status ?? video?.status)}
              label={status?.status ?? video?.status ?? 'no video'}
            />
          </div>
          {video ? (
            <div className="mt-2 font-mono text-xs text-muted">
              {video.camera_id}
              <br />
              {video.video_id}
            </div>
          ) : null}
          <div className="mt-4 text-xs text-muted">{user?.email}</div>
          <button
            type="button"
            onClick={() => void logout()}
            className="mt-2 text-sm text-muted hover:text-ink"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1 px-8 py-8">
        {error ? (
          <div className="mb-6 max-w-3xl">
            <ErrorBanner message={error} />
          </div>
        ) : null}
        {loading ? (
          <p className="font-mono text-sm text-muted">Loading workspace…</p>
        ) : null}
        {!loading && tab === 'conversation' ? (
          <ConversationTab video={video} status={status} />
        ) : null}
        {!loading && tab === 'video' ? (
          <VideoTab video={video} status={status} onUploaded={adopt} />
        ) : null}
        {!loading && tab === 'events' ? (
          <EventsTab video={video} status={status} events={events} />
        ) : null}
      </main>
    </div>
  )
}
