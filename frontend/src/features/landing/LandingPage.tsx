import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '../../components/Button.tsx'
import { clockLabel } from '../../lib/format.ts'

const PIPELINE = [
  { n: '01', title: 'Ingest', detail: 'Store the file. Assign video_id and camera_id.' },
  { n: '02', title: 'Sample frames', detail: 'Fixed interval or scene-change. Not every frame.' },
  { n: '03', title: 'Detect', detail: 'YOLO11 with pretrained COCO weights.' },
  { n: '04', title: 'Construct events', detail: 'Group detections into time-bounded records.' },
  { n: '05', title: 'Caption', detail: 'Qwen2.5-VL on flagged frames. Rule-based fallback.' },
  { n: '06', title: 'Index', detail: 'Embed captions and metadata in ChromaDB.' },
  { n: '07', title: 'Query', detail: 'LangGraph answer with timestamp, camera, thumbnail.' },
]

export function LandingPage() {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000)
    return () => window.clearInterval(id)
  }, [])

  return (
    <div className="min-h-screen bg-base text-ink">
      <header className="flex items-end justify-between border-b border-border px-8 py-4">
        <div>
          <div className="text-lg font-semibold tracking-tight">SentinelRAG</div>
          <div className="text-sm text-muted">Video-surveillance RAG</div>
        </div>
        <div className="text-right font-mono text-sm text-muted">
          <div>Phase 1  offline batch</div>
          <div>{clockLabel(now)}</div>
        </div>
      </header>

      <main className="px-8 py-12">
        <p className="max-w-xl text-2xl font-medium leading-snug">
          Upload recorded CCTV. Ask what happened. Every answer cites a timestamp, a camera, and a
          frame.
        </p>
        <p className="mt-4 max-w-xl text-muted">
          Index once. Query as often as you need. This is not a live camera feed — footage is
          processed in batch, then searched in natural language.
        </p>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Link to="/auth?mode=register">
            <Button>Open console</Button>
          </Link>
          <Link to="/auth?mode=login" className="text-sm text-muted hover:text-ink">
            Sign in
          </Link>
        </div>

        <section className="mt-16 max-w-2xl">
          <h2 className="mb-4 text-sm text-muted">Batch pipeline</h2>
          <ol className="divide-y divide-border border-y border-border">
            {PIPELINE.map((stage) => (
              <li key={stage.n} className="grid grid-cols-[3rem_1fr] gap-4 py-3">
                <span className="font-mono text-sm text-sage">{stage.n}</span>
                <div>
                  <div className="font-medium">{stage.title}</div>
                  <div className="text-sm text-muted">{stage.detail}</div>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="mt-16 max-w-2xl">
          <h2 className="mb-4 text-sm text-muted">Grounded answer</h2>
          <div className="border border-border bg-surface p-5">
            <p className="max-w-prose">
              Yes. A person wearing a red jacket entered through the main doors. Observed
              00:14:20–00:14:45 on cam-01.
            </p>
            <div className="mt-5 border-t border-border pt-4 font-mono text-sm text-muted">
              <div>00:14:20–00:14:45</div>
              <div>cam-01  vid_7f3a1c  evt_14a2  0.93</div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
