import React from 'react'
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
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
        <path d="M3 4h14v10H9.5L6 17l-1.5-3H3V4z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
        <path d="M6 8h8M6 11h5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      </svg>
    ),
  },
  {
    id: 'video',
    label: 'Ingest Footage',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
        <rect x="2" y="4" width="11" height="12" rx="1.5" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M13 8l5-3v10l-5-3V8z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
      </svg>
    ),
  },
  {
    id: 'events',
    label: 'Event Index',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
        <rect x="2" y="2" width="16" height="16" rx="1.5" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M6 6h8M6 10h8M6 14h6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
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
    <span className="font-mono text-xs text-[#CCCCCC] tabular-nums font-medium">
      {pad(time.getHours())}:{pad(time.getMinutes())}:{pad(time.getSeconds())}
    </span>
  )
}

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
    <div className="flex h-screen bg-black text-[#EEEEEE] overflow-hidden font-sans">

      {/* ── SIDEBAR ─────────────────────────────────────────── */}
      <aside className="flex w-64 shrink-0 flex-col border-r border-[#1f1f1f] bg-[#050505]">

        {/* Logo */}
        <div className="flex items-center gap-2.5 border-b border-[#1f1f1f] px-5 py-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#CB2957] shadow-[0_0_12px_rgba(203,41,87,0.4)]">
            <svg width="15" height="15" viewBox="0 0 14 14" fill="none">
              <rect x="0" y="3" width="9" height="8" rx="1.2" fill="white"/>
              <path d="M9 5.5l4.5-2.5v8l-4.5-2.5V5.5z" fill="white"/>
            </svg>
          </div>
          <div>
            <div className="text-sm font-bold tracking-tight leading-none text-white">SENTINEL<span className="text-[#CB2957]">RAG</span></div>
            <div className="text-[10px] text-[#AAAAAA] font-medium tracking-wider uppercase mt-1">Operator Console</div>
          </div>
        </div>

        {/* System Status */}
        <div className="border-b border-[#181818] px-5 py-3 bg-[#080808]">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#999999]">System Status</span>
            <LiveClock />
          </div>
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e] animate-pulse" />
            <span className="text-[11px] font-semibold text-[#22c55e] uppercase tracking-wider">Online & Active</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 space-y-1">
          <div className="px-5 py-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#888888]">Navigation</span>
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
                  'group flex w-full items-center gap-3 px-5 py-2.5 text-left transition-all duration-150 text-xs font-semibold',
                  active
                    ? 'border-r-4 border-[#CB2957] bg-[#CB2957]/10 text-white'
                    : 'border-r-4 border-transparent text-[#AAAAAA] hover:text-white hover:bg-[#111111]',
                ].join(' ')}
              >
                <span className={active ? 'text-[#CB2957]' : 'text-[#888888] group-hover:text-[#CCCCCC]'}>
                  {icon}
                </span>
                <span>{label}</span>
                {eventCount !== null && (
                  <span className="ml-auto font-mono text-[10px] rounded-full bg-[#CB2957]/20 text-[#CB2957] border border-[#CB2957]/30 px-1.5 py-0.5 font-bold">
                    {eventCount}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Active Video Info */}
        {video && (
          <div className="border-t border-[#1f1f1f] px-5 py-3 space-y-1.5 bg-[#080808]">
            <div className="text-[10px] font-bold uppercase tracking-wider text-[#888888]">Active Feed Stream</div>
            <div className="flex items-start gap-2">
              <StatusDot tone={statusTone} label={currentStatus ?? 'unknown'} pulse={isProcessing} />
            </div>
            <div className="text-xs text-[#AAAAAA] leading-relaxed break-all font-mono pt-0.5">
              <div className="text-white font-semibold font-sans">{video.camera_id}</div>
              <div className="text-[10px] text-[#888888]">{video.video_id}</div>
            </div>
          </div>
        )}

        {/* User / Logout */}
        <div className="border-t border-[#1f1f1f] px-5 py-3 bg-[#050505]">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-[#888888]">Operator</div>
              <div className="text-xs font-medium text-[#EEEEEE] truncate max-w-[130px]">{user?.email}</div>
            </div>
            <button
              type="button"
              onClick={() => void logout()}
              className="text-[11px] font-semibold uppercase tracking-wider text-[#CCCCCC] hover:text-[#CB2957] bg-[#141414] border border-[#262626] px-2.5 py-1 rounded transition-colors"
            >
              Exit
            </button>
          </div>
        </div>
      </aside>

      {/* ── MAIN CONTENT ─────────────────────────────────────── */}
      <main className="flex flex-1 flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center justify-between border-b border-[#1f1f1f] bg-[#050505] px-6 py-3 shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="h-2 w-2 rounded-full bg-[#CB2957] animate-pulse" />
            <h2 className="text-sm font-semibold text-[#EEEEEE]">
              {tab === 'conversation' ? 'Intelligence Query Console'
               : tab === 'video' ? 'CCTV Footage Ingestion & Pipeline'
               : 'Event Index Catalog'}
            </h2>
          </div>
          {video && (
            <div className="flex items-center gap-3">
              <span className="text-xs text-[#CCCCCC] font-medium bg-[#111111] px-2.5 py-1 rounded border border-[#222222]">
                📹 {video.camera_id} · <span className="text-white">{video.original_filename}</span>
              </span>
              {status && (
                <StatusDot tone={statusTone} label={`${status.progress.toFixed(0)}% Complete`} pulse={isProcessing} />
              )}
            </div>
          )}
        </div>

        {/* Content area */}
        <div className="flex-1 overflow-y-auto">
          {error ? (
            <div className="m-6 max-w-2xl">
              <ErrorBanner message={error} />
            </div>
          ) : null}

          {loading ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center space-y-2.5">
                <div className="mx-auto h-8 w-8 rounded-full border border-[#CB2957]/30 bg-[#CB2957]/10 flex items-center justify-center">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#CB2957] animate-ping" />
                </div>
                <span className="text-xs font-semibold text-[#DDDDDD] uppercase tracking-wider block">Loading workspace session…</span>
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
