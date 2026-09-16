import { Link } from 'react-router-dom'

const FEATURES = [
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="8.5" stroke="#CB2957" strokeWidth="1.2"/>
        <circle cx="10" cy="10" r="4" stroke="#CB2957" strokeWidth="1.2"/>
        <circle cx="10" cy="10" r="1.5" fill="#CB2957"/>
        <line x1="10" y1="1.5" x2="10" y2="4" stroke="#CB2957" strokeWidth="1.2"/>
        <line x1="10" y1="16" x2="10" y2="18.5" stroke="#CB2957" strokeWidth="1.2"/>
        <line x1="1.5" y1="10" x2="4" y2="10" stroke="#CB2957" strokeWidth="1.2"/>
        <line x1="16" y1="10" x2="18.5" y2="10" stroke="#CB2957" strokeWidth="1.2"/>
      </svg>
    ),
    title: 'YOLO11 Detection',
    desc: 'Frame-accurate object detection across person, vehicle, and baggage classes at every 0.8s sample.',
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <rect x="1.5" y="4" width="12" height="10" rx="1.5" stroke="#CB2957" strokeWidth="1.2"/>
        <path d="M13.5 8l5-3v10l-5-3V8z" stroke="#CB2957" strokeWidth="1.2" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'Gemini Vision Captioning',
    desc: 'Multimodal AI inspects each flagged frame: clothing colors, object counts, movement direction, and text signs.',
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M3 10l4 4 10-10" stroke="#CB2957" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
        <circle cx="10" cy="10" r="8.5" stroke="#CB2957" strokeWidth="1.2" strokeDasharray="3 2"/>
      </svg>
    ),
    title: 'pgvector Semantic Search',
    desc: 'Dense 768-d embeddings stored in Supabase pgvector with hybrid BM25 fallback for exact-match retrieval.',
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M4 14l3-3 3 3 6-8" stroke="#CB2957" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
        <rect x="1.5" y="2" width="17" height="16" rx="1.5" stroke="#CB2957" strokeWidth="1.2"/>
      </svg>
    ),
    title: 'Grounded NL Answers',
    desc: 'Every answer is grounded to a timestamp window, camera ID, and cited CCTV thumbnail. No hallucinations.',
  },
]

const PIPELINE = [
  { step: '01', title: 'Upload CCTV', detail: 'Drag-and-drop any MP4 / MOV / MKV recording. Stored in Supabase Storage.' },
  { step: '02', title: 'Frame Sampling', detail: 'Adaptive frame extraction at 0.8s intervals. Scene-change detection optional.' },
  { step: '03', title: 'YOLO11 Detect', detail: 'Object detection on every frame. Events grouped by class & temporal gap.' },
  { step: '04', title: 'Gemini Caption', detail: 'VLM inspects representative frames for rich security analyst descriptions.' },
  { step: '05', title: 'pgvector Index', detail: '768-d embeddings committed to Supabase. Index locked until complete.' },
  { step: '06', title: 'Query', detail: 'Natural-language Q&A with visual evidence citations and timestamp grounding.' },
]

export function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-[#EEEEEE] surveillance-grid">
      {/* TOP BAR */}
      <header className="sticky top-0 z-50 flex items-center justify-between border-b border-[#1a1a1a] bg-black/90 backdrop-blur-md px-8 py-4">
        <div className="flex items-center gap-3">
          {/* Logo mark */}
          <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-[#CB2957]">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <rect x="0" y="3" width="9" height="8" rx="1.2" fill="white"/>
              <path d="M9 5.5l4.5-2.5v8l-4.5-2.5V5.5z" fill="white"/>
            </svg>
          </div>
          <span className="font-mono text-sm font-semibold tracking-tight">SENTINEL<span className="text-[#CB2957]">RAG</span></span>
          <span className="font-mono text-[10px] text-[#888888] uppercase tracking-widest border border-[#222222] px-2 py-0.5 rounded-sm">v1.0</span>
        </div>
        <nav className="flex items-center gap-6">
          <a href="#pipeline" className="text-xs font-mono uppercase tracking-widest text-[#AAAAAA] hover:text-[#CB2957] transition-colors">
            Pipeline
          </a>
          <a href="#features" className="text-xs font-mono uppercase tracking-widest text-[#AAAAAA] hover:text-[#CB2957] transition-colors">
            Features
          </a>
          <Link
            to="/auth?mode=login"
            className="font-mono text-xs uppercase tracking-widest text-[#DDDDDD] border border-[#333333] px-4 py-2 rounded-sm hover:border-[#CB2957] hover:text-white transition-all"
          >
            Operator Login
          </Link>
          <Link
            to="/auth?mode=register"
            className="font-mono text-xs uppercase tracking-widest text-white bg-[#CB2957] border border-[#CB2957] px-4 py-2 rounded-sm hover:bg-[#a8213e] transition-all shadow-[0_0_16px_rgba(203,41,87,0.3)]"
          >
            Access System
          </Link>
        </nav>
      </header>

      {/* HERO */}
      <section className="relative overflow-hidden px-8 pb-24 pt-28">
        {/* Red glow blob */}
        <div className="pointer-events-none absolute left-1/2 top-0 -translate-x-1/2 h-[500px] w-[800px] rounded-full bg-[#CB2957]/5 blur-[120px]" />

        {/* REC badge */}
        <div className="mb-8 flex items-center justify-center gap-2">
          <span className="inline-flex items-center gap-2 border border-[#CB2957]/40 bg-[#CB2957]/10 px-4 py-1.5 rounded-sm font-mono text-xs uppercase tracking-widest text-[#CB2957]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#CB2957] pulse-dot"/>
            Live Intelligence System
          </span>
        </div>

        <div className="relative mx-auto max-w-5xl text-center">
          <h1 className="text-6xl font-bold tracking-tight leading-none">
            <span className="text-[#EEEEEE]">Ask your</span>
            <br />
            <span className="text-[#CB2957]">CCTV footage</span>
            <br />
            <span className="text-[#EEEEEE]">anything.</span>
          </h1>
          <p className="mx-auto mt-8 max-w-2xl text-base text-[#AAAAAA] leading-relaxed">
            SentinelRAG transforms recorded surveillance video into a queryable intelligence layer.
            Upload footage → AI indexes every frame → ask natural-language questions and get
            timestamp-grounded answers with visual evidence citations.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              to="/auth?mode=register"
              className="inline-flex items-center gap-2 bg-[#CB2957] text-white font-mono text-sm uppercase tracking-widest px-8 py-3.5 rounded-sm hover:bg-[#a8213e] transition-all shadow-[0_0_24px_rgba(203,41,87,0.4)] hover:shadow-[0_0_40px_rgba(203,41,87,0.6)]"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="0" y="2.5" width="10" height="9" rx="1.2" fill="white" fillOpacity="0.9"/>
                <path d="M10 5l3.5-2v8L10 9V5z" fill="white" fillOpacity="0.9"/>
              </svg>
              Start Surveillance Session
            </Link>
            <a
              href="#pipeline"
              className="inline-flex items-center gap-2 text-[#AAAAAA] font-mono text-sm uppercase tracking-widest px-8 py-3.5 rounded-sm border border-[#333333] hover:border-[#CB2957] hover:text-[#EEEEEE] transition-all"
            >
              View Architecture
            </a>
          </div>
        </div>

        {/* Fake CCTV monitor strip */}
        <div className="mx-auto mt-20 max-w-5xl">
          <div className="rounded-sm border border-[#1a1a1a] bg-[#050505] overflow-hidden">
            {/* Monitor header */}
            <div className="flex items-center justify-between border-b border-[#1a1a1a] px-5 py-2.5">
              <div className="flex items-center gap-3">
                <span className="h-1.5 w-1.5 rounded-full bg-[#CB2957] pulse-dot"/>
                <span className="font-mono text-[10px] uppercase tracking-widest text-[#777777]">CAM-01 · LIVE FEED SIMULATION</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="font-mono text-[10px] text-[#AAAAAA]">REC</span>
                <span className="font-mono text-[10px] text-[#AAAAAA]">1920×1080</span>
                <span className="font-mono text-[10px] text-[#AAAAAA]">H.264</span>
              </div>
            </div>
            {/* Monitor body — checkerboard placeholder */}
            <div className="relative h-64 bg-[#050505] flex items-center justify-center overflow-hidden scanlines">
              <div className="absolute inset-0 opacity-5"
                style={{
                  backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 30px, #CB2957 30px, #CB2957 31px), repeating-linear-gradient(90deg, transparent, transparent 30px, #CB2957 30px, #CB2957 31px)',
                }}
              />
              <div className="relative z-10 text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-sm border border-[#1a1a1a] bg-[#0a0a0a]">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-[#CB2957]">
                    <rect x="2" y="6" width="14" height="12" rx="1.5" stroke="currentColor" strokeWidth="1.4"/>
                    <path d="M16 10l6-4v12l-6-4V10z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
                    <circle cx="9" cy="12" r="2.5" stroke="currentColor" strokeWidth="1.2"/>
                  </svg>
                </div>
                <p className="font-mono text-xs text-[#777777] uppercase tracking-widest">Upload footage to begin indexing</p>
              </div>
              {/* Timestamp overlay */}
              <div className="absolute bottom-3 left-4 font-mono text-[10px] text-[#AAAAAA]">
                2024-10-14 · 09:15:32 UTC
              </div>
              <div className="absolute bottom-3 right-4 font-mono text-[10px] text-[#AAAAAA]">
                SENTINEL-CAM-01
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PIPELINE */}
      <section id="pipeline" className="border-t border-[#111111] px-8 py-24">
        <div className="mx-auto max-w-5xl">
          <div className="mb-3 font-mono text-[10px] uppercase tracking-widest text-[#CB2957]">Processing Architecture</div>
          <h2 className="text-3xl font-bold text-[#EEEEEE]">Six-stage ingestion pipeline.</h2>
          <p className="mt-3 text-sm text-[#AAAAAA] max-w-xl">
            Every video is processed through a deterministic pipeline before the query interface unlocks.
          </p>

          <div className="mt-14 grid grid-cols-2 gap-px bg-[#111111] border border-[#111111] rounded-sm overflow-hidden md:grid-cols-3">
            {PIPELINE.map((item) => (
              <div key={item.step} className="bg-black p-6 hover:bg-[#050505] transition-colors group">
                <div className="font-mono text-[10px] text-[#CB2957] mb-3 group-hover:text-[#e0325f] transition-colors">{item.step}</div>
                <div className="text-sm font-semibold text-[#EEEEEE] mb-2">{item.title}</div>
                <div className="text-xs text-[#999999] leading-relaxed">{item.detail}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="border-t border-[#111111] px-8 py-24">
        <div className="mx-auto max-w-5xl">
          <div className="mb-3 font-mono text-[10px] uppercase tracking-widest text-[#CB2957]">System Capabilities</div>
          <h2 className="text-3xl font-bold text-[#EEEEEE]">Production-grade intelligence stack.</h2>

          <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-2">
            {FEATURES.map((feat) => (
              <div
                key={feat.title}
                className="group relative rounded-sm border border-[#1a1a1a] bg-[#050505] p-6 hover:border-[#CB2957]/30 transition-all duration-300"
              >
                <div className="absolute inset-0 rounded-sm bg-[#CB2957]/0 group-hover:bg-[#CB2957]/3 transition-colors duration-300"/>
                <div className="relative">
                  <div className="mb-4">{feat.icon}</div>
                  <h3 className="text-sm font-semibold text-[#EEEEEE] mb-2">{feat.title}</h3>
                  <p className="text-xs text-[#AAAAAA] leading-relaxed">{feat.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-[#111111] px-8 py-24">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-3 font-mono text-[10px] uppercase tracking-widest text-[#CB2957]">Deploy</div>
          <h2 className="text-4xl font-bold text-[#EEEEEE]">Query your footage now.</h2>
          <p className="mt-4 text-sm text-[#AAAAAA] max-w-md mx-auto">
            Register an operator account, upload a recorded video, and start asking questions within minutes.
          </p>
          <div className="mt-10">
            <Link
              to="/auth?mode=register"
              className="inline-flex items-center gap-2 bg-[#CB2957] text-white font-mono text-sm uppercase tracking-widest px-10 py-4 rounded-sm hover:bg-[#a8213e] transition-all shadow-[0_0_24px_rgba(203,41,87,0.4)]"
            >
              Access System →
            </Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-[#111111] px-8 py-8">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-5 w-5 items-center justify-center rounded-sm bg-[#CB2957]">
              <svg width="10" height="10" viewBox="0 0 14 14" fill="none">
                <rect x="0" y="3" width="9" height="8" rx="1.2" fill="white"/>
                <path d="M9 5.5l4.5-2.5v8l-4.5-2.5V5.5z" fill="white"/>
              </svg>
            </div>
            <span className="font-mono text-xs text-[#AAAAAA]">SENTINELRAG</span>
          </div>
          <div className="font-mono text-[10px] text-[#AAAAAA] uppercase tracking-widest">
            YOLO11 · Gemini 2.5 Flash · Supabase pgvector
          </div>
        </div>
      </footer>
    </div>
  )
}
