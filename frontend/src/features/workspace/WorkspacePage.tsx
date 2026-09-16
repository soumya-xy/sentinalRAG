import { Navigate, useSearchParams } from 'react-router-dom'

import { ErrorBanner } from '../../components/ErrorBanner.tsx'
import { StatusDot, statusToTone } from '../../components/StatusDot.tsx'
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

const NAV_ITEMS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  {
    id: 'conversation',
    label: 'Intelligence Query',
    icon: (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M2 2h10v8H8.5L7 12l-1.5-2H2V2z" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round"/>
        <path d="M4 5h6M4 7h4" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
      </svg>
    ),
  },
  {
    id: 'video',
    label: 'Ingest Footage',
    icon: (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <rect x="0.75" y="3" width="8.5" height="8" rx="1" stroke="currentColor" strokeWidth="1.1"/>
        <path d="M9.25 6l4-2v6l-4-2V6z" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round"/>
      </svg>
    ),
  },
  {
    id: 'events',
    label: 'Event Index',
    icon: (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <rect x="1" y="1" width="12" height="12" rx="1" stroke="currentColor" strokeWidth="1.1"/>
        <path d="M4 4h6M4 7h6M4 10h4" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
      </svg>
    ),
  },
]

// Live clock
function LiveClock() {
  const [time, setTime] = React.useState(() => new Date())
  React.useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  const pad = (n: number) => String(n).padStart(2, '0')
  return (
    <span className="font-mono text-[10px] text-[#888888] tabular-nums">
      {pad(time.getHours())}:{pad(time.getMinutes())}:{pad(time.getSeconds())}
    </span>
  )
}

import React from 'react'

export function WorkspacePage() {
  const { user, ready, logout } = useAuth()
  const [params, setParams] = useSearchParams()
  const tab = asTab(params.get('tab'))
  const { video, status, events, error, loading, adopt } = useActiveVideo()

  if (ready && !user) return <Navigate to="/auth?mode=login" replace />

  function go(next: Tab) {
    setParams(next === 'conversation' ? {} : { tab: next })
  }

  const currentStatus = status?.status ?? video?.status
  const statusTone = statusToTone(currentStatus)
  const isProcessing = currentStatus === 'processing' || currentStatus === 'uploaded'

  return (
    <div className="flex h-screen bg-black text-[#EEEEEE] overflow-hidden">

      {/* ── SIDEBAR ─────────────────────────────────────────── */}
      <aside className="flex w-64 shrink-0 flex-col border-r border-[#1a1a1a] bg-[#050505]">

        {/* Logo */}
        <div className="flex items-center gap-3 border-b border-[#1a1a1a] px-5 py-4">
          <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-[#CB2957]">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <rect x="0" y="3" width="9" height="8" rx="1.2" fill="white"/>
              <path d="M9 5.5l4.5-2.5v8l-4.5-2.5V5.5z" fill="white"/>
            </svg>
          </div>
          <div>
            <div className="font-mono text-sm font-semibold tracking-tight leading-none">SENTINEL<span className="text-[#CB2957]">RAG</span></div>
            <div className="font-mono text-[9px] text-[#888888] uppercase tracking-widest mt-0.5">Operator Console</div>
          </div>
        </div>

        {/* System Status */}
        <div className="border-b border-[#111111] px-5 py-3">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#777777]">System Status</span>
            <LiveClock />
          </div>
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e] pulse-dot" />
            <span className="font-mono text-[10px] text-[#22c55e] uppercase tracking-wide">Online</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3">
          <div className="px-5 py-2">
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#777777]">Navigation</span>
          </div>
          {NAV_ITEMS.map(({ id, label, icon }) => {
            const active = tab === id
            const eventCount = id === 'events' && events.length > 0 ? events.length : null
            return (
              <button
                key={id}
                type="button"
                onClick={() => go(id)}
                className={[
                  'group flex w-full items-center gap-3 px-5 py-2.5 text-left transition-all duration-150',
                  active
                    ? 'border-r-2 border-[#CB2957] bg-[#CB2957]/8 text-[#EEEEEE]'
                    : 'border-r-2 border-transparent text-[#999999] hover:text-[#DDDDDD] hover:bg-[#0a0a0a]',
                ].join(' ')}
              >
                <span className={active ? 'text-[#CB2957]' : 'text-[#888888] group-hover:text-[#888888]'}>
                  {icon}
                </span>
                <span className="text-xs font-medium">{label}</span>
                {eventCount !== null && (
                  <span className="ml-auto font-mono text-[9px] rounded-sm bg-[#CB2957]/15 text-[#CB2957] border border-[#CB2957]/20 px-1.5 py-0.5">
                    {eventCount}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Active Video Info */}
        {video && (
          <div className="border-t border-[#111111] px-5 py-4 space-y-2">
            <div className="font-mono text-[9px] uppercase tracking-widest text-[#777777]">Active Feed</div>
            <div className="flex items-start gap-2">
              <StatusDot tone={statusTone} label={currentStatus ?? 'unknown'} pulse={isProcessing} />
            </div>
            <div className="font-mono text-[10px] text-[#888888] leading-relaxed break-all">
              <div className="text-[#999999]">{video.camera_id}</div>
              <div>{video.video_id}</div>
            </div>
          </div>
        )}

        {/* User / Logout */}
        <div className="border-t border-[#111111] px-5 py-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-mono text-[9px] uppercase tracking-widest text-[#777777] mb-1">Operator</div>
              <div className="text-xs text-[#999999] truncate max-w-[140px]">{user?.email}</div>
            </div>
            <button
              type="button"
              onClick={() => void logout()}
              className="font-mono text-[10px] uppercase tracking-widest text-[#888888] hover:text-[#CB2957] transition-colors"
            >
              Exit
            </button>
          </div>
        </div>
      </aside>

      {/* ── MAIN CONTENT ─────────────────────────────────────── */}
      <main className="flex flex-1 flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center justify-between border-b border-[#1a1a1a] bg-[#050505] px-8 py-3 shrink-0">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-[#CB2957] pulse-dot" />
            <span className="font-mono text-[10px] uppercase tracking-widest text-[#888888]">
              {tab === 'conversation' ? 'Intelligence Query Interface'
               : tab === 'video' ? 'Footage Ingestion'
               : 'Event Index Browser'}
            </span>
          </div>
          {video && (
            <div className="flex items-center gap-4">
              <span className="font-mono text-[10px] text-[#777777] uppercase tracking-wide">
                {video.camera_id} · {video.original_filename}
              </span>
              {status && (
                <StatusDot tone={statusTone} label={`${status.progress.toFixed(0)}%`} pulse={isProcessing} />
              )}
            </div>
          )}
        </div>

        {/* Content area */}
        <div className="flex-1 overflow-y-auto">
          {error ? (
            <div className="m-8 max-w-2xl">
              <ErrorBanner message={error} />
            </div>
          ) : null}

          {loading ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mx-auto mb-4 h-8 w-8 rounded-sm border border-[#CB2957]/20 bg-[#CB2957]/5 flex items-center justify-center">
                  <span className="h-2 w-2 rounded-full bg-[#CB2957] pulse-dot" />
                </div>
                <span className="font-mono text-xs text-[#888888] uppercase tracking-widest">Loading workspace…</span>
              </div>
            </div>
          ) : null}

          {!loading && tab === 'conversation' && <ConversationTab video={video} status={status} />}
          {!loading && tab === 'video' && <VideoTab video={video} status={status} onUploaded={adopt} />}
          {!loading && tab === 'events' && <EventsTab video={video} status={status} events={events} />}
        </div>
      </main>
    </div>
  )
}
