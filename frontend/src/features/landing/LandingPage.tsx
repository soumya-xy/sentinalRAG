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
    title: 'YOLO11 Object Detection',
    desc: 'Frame-accurate object detection across person, vehicle, and baggage classes at adaptive frame intervals.',
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <rect x="1.5" y="4" width="12" height="10" rx="1.5" stroke="#CB2957" strokeWidth="1.2"/>
        <path d="M13.5 8l5-3v10l-5-3V8z" stroke="#CB2957" strokeWidth="1.2" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'Gemini 2.5 Vision Captioning',
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
    title: 'Grounded NL Answers & Citations',
    desc: 'Every answer is grounded to a timestamp window, camera ID, and cited CCTV thumbnail. Zero hallucinations.',
  },
]

const PIPELINE = [
  { step: '01', title: 'Upload CCTV', detail: 'Drag-and-drop any MP4 / MOV / MKV recording. Stored securely.' },
  { step: '02', title: 'Frame Sampling', detail: 'Adaptive frame extraction at 0.8s intervals.' },
  { step: '03', title: 'YOLO11 Detect', detail: 'Real-time object detection on every sampled frame.' },
  { step: '04', title: 'Gemini Caption', detail: 'VLM generates detailed security analyst descriptions.' },
  { step: '05', title: 'pgvector Index', detail: '768-d embeddings committed to Supabase vector storage.' },
  { step: '06', title: 'Query & Cite', detail: 'Natural language Q&A with visual evidence citations.' },
]

export function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-[#EEEEEE] font-sans selection:bg-[#CB2957] selection:text-white">
      {/* TOP BAR */}
      <header className="sticky top-0 z-50 flex items-center justify-between border-b border-[#1f1f1f] bg-black/90 backdrop-blur-md px-6 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#CB2957] shadow-[0_0_12px_rgba(203,41,87,0.4)]">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <rect x="0" y="3" width="9" height="8" rx="1.2" fill="white"/>
              <path d="M9 5.5l4.5-2.5v8l-4.5-2.5V5.5z" fill="white"/>
            </svg>
          </div>
          <span className="text-sm font-bold tracking-tight text-white">SENTINEL<span className="text-[#CB2957]">RAG</span></span>
          <span className="text-[11px] font-semibold text-[#AAAAAA] border border-[#262626] px-2 py-0.5 rounded-full">v1.0</span>
        </div>
        <nav className="flex items-center gap-5">
          <a href="#pipeline" className="text-xs font-medium text-[#AAAAAA] hover:text-white transition-colors">
            Architecture
          </a>
          <a href="#features" className="text-xs font-medium text-[#AAAAAA] hover:text-white transition-colors">
            Capabilities
          </a>
          <Link
            to="/auth?mode=login"
            className="text-xs font-semibold text-[#DDDDDD] border border-[#2a2a2a] px-3.5 py-1.5 rounded-md hover:border-[#CB2957] hover:text-white transition-all"
          >
            Operator Login
          </Link>
          <Link
            to="/auth?mode=register"
            className="text-xs font-semibold text-white bg-[#CB2957] border border-[#CB2957] px-4 py-1.5 rounded-md hover:bg-[#a8213e] transition-all shadow-[0_0_12px_rgba(203,41,87,0.4)]"
          >
            Access System
          </Link>
        </nav>
      </header>

      {/* HERO */}
      <section className="relative overflow-hidden px-6 pb-20 pt-20">
        <div className="pointer-events-none absolute left-1/2 top-0 -translate-x-1/2 h-[400px] w-[600px] rounded-full bg-[#CB2957]/8 blur-[100px]" />

        <div className="mb-6 flex items-center justify-center">
          <span className="inline-flex items-center gap-2 border border-[#CB2957]/40 bg-[#CB2957]/10 px-3.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider text-[#CB2957]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#CB2957] animate-pulse"/>
            Enterprise Surveillance Intelligence Platform
          </span>
        </div>

        <div className="relative mx-auto max-w-4xl text-center space-y-4">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight leading-tight text-white">
            Ask your <span className="text-[#CB2957]">CCTV footage</span> anything.
          </h1>
          <p className="mx-auto max-w-2xl text-sm sm:text text-[#CCCCCC] leading-relaxed font-normal">
            SentinelRAG transforms recorded CCTV surveillance footage into an interactive knowledge engine.
            Upload footage → AI indexes every frame → query in natural language with timestamp-grounded visual evidence.
          </p>
          <div className="pt-3 flex items-center justify-center gap-3">
            <Link
              to="/auth?mode=register"
              className="inline-flex items-center gap-2 bg-[#CB2957] text-white text-xs sm:text-sm font-semibold px-6 py-3 rounded-lg hover:bg-[#a8213e] transition-all shadow-[0_0_20px_rgba(203,41,87,0.4)]"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="0" y="2.5" width="10" height="9" rx="1.2" fill="white"/>
                <path d="M10 5l3.5-2v8L10 9V5z" fill="white"/>
              </svg>
              Start Surveillance Console
            </Link>
            <a
              href="#pipeline"
              className="inline-flex items-center gap-2 text-[#EEEEEE] text-xs sm:text-sm font-semibold px-6 py-3 rounded-lg border border-[#2c2c2c] bg-[#0d0d0d] hover:border-[#CB2957] hover:text-white transition-all"
            >
              View System Architecture
            </a>
          </div>
        </div>

        {/* CCTV Monitor Preview */}
        <div className="mx-auto mt-12 max-w-4xl">
          <div className="rounded-lg border border-[#222222] bg-[#080808] overflow-hidden shadow-xl">
            <div className="flex items-center justify-between border-b border-[#1c1c1c] px-5 py-2.5 bg-[#050505]">
              <div className="flex items-center gap-2.5">
                <span className="h-1.5 w-1.5 rounded-full bg-[#CB2957] animate-pulse"/>
                <span className="text-[11px] font-semibold text-[#AAAAAA] uppercase tracking-wider">CAM-01 · LIVE STREAM MONITOR SIMULATION</span>
              </div>
              <div className="flex items-center gap-3 font-mono text-[11px] text-[#888888]">
                <span>1920×1080</span>
                <span>30 FPS</span>
                <span>H.264</span>
              </div>
            </div>
            <div className="relative h-60 bg-[#000000] flex items-center justify-center overflow-hidden">
              <div className="relative z-10 text-center space-y-2 p-4">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-[#222222] bg-[#0c0c0c]">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-[#CB2957]">
                    <rect x="2" y="6" width="14" height="12" rx="1.5" stroke="currentColor" strokeWidth="1.5"/>
                    <path d="M16 10l6-4v12l-6-4V10z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
                    <circle cx="9" cy="12" r="2.5" stroke="currentColor" strokeWidth="1.5"/>
                  </svg>
                </div>
                <h3 className="text-sm font-semibold text-white">Upload Video Stream to Begin Automated Indexing</h3>
                <p className="text-xs text-[#888888] max-w-md mx-auto">YOLO11 object tracking and Gemini 2.5 Flash visual captioning will index every frame into Supabase pgvector.</p>
              </div>
              <div className="absolute bottom-3 left-4 font-mono text-[11px] text-[#888888]">
                LIVE FEED · 2026-09-18 21:52:45 UTC
              </div>
              <div className="absolute bottom-3 right-4 font-mono text-[11px] text-[#888888]">
                SENTINEL-CAM-01
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PIPELINE */}
      <section id="pipeline" className="border-t border-[#1a1a1a] bg-[#050505] px-6 py-16">
        <div className="mx-auto max-w-4xl">
          <div className="mb-1 text-xs font-bold uppercase tracking-wider text-[#CB2957]">Processing Architecture</div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white">Six-Stage Multimodal Ingestion Pipeline</h2>
          <p className="mt-2 text-sm text-[#AAAAAA] max-w-xl leading-relaxed">
            Every recording goes through a deterministic 6-stage computer vision & vector embedding pipeline.
          </p>

          <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
            {PIPELINE.map((item) => (
              <div key={item.step} className="bg-[#0a0a0a] p-4 rounded-lg border border-[#222222] hover:border-[#CB2957]/40 transition-colors group space-y-1.5">
                <div className="font-mono text-xs font-bold text-[#CB2957]">{item.step}</div>
                <div className="text-sm font-semibold text-white">{item.title}</div>
                <div className="text-xs text-[#AAAAAA] leading-relaxed">{item.detail}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="border-t border-[#1a1a1a] px-6 py-16">
        <div className="mx-auto max-w-4xl">
          <div className="mb-1 text-xs font-bold uppercase tracking-wider text-[#CB2957]">System Capabilities</div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white">Production-Grade Intelligence Stack</h2>

          <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2">
            {FEATURES.map((feat) => (
              <div
                key={feat.title}
                className="group relative rounded-lg border border-[#222222] bg-[#080808] p-5 hover:border-[#CB2957]/40 transition-all duration-300 space-y-2"
              >
                <div>{feat.icon}</div>
                <h3 className="text-base font-semibold text-white">{feat.title}</h3>
                <p className="text-xs sm:text-sm text-[#AAAAAA] leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-[#1a1a1a] bg-[#050505] px-6 py-16 text-center">
        <div className="mx-auto max-w-2xl space-y-3">
          <div className="text-xs font-bold uppercase tracking-wider text-[#CB2957]">Ready to Deploy</div>
          <h2 className="text-3xl font-bold text-white">Start Querying Your Footage Now</h2>
          <p className="text-sm text-[#AAAAAA] max-w-md mx-auto">
            Register your operator account, upload a CCTV recording, and start asking natural language questions.
          </p>
          <div className="pt-4">
            <Link
              to="/auth?mode=register"
              className="inline-flex items-center gap-2 bg-[#CB2957] text-white text-xs sm:text-sm font-semibold px-8 py-3.5 rounded-lg hover:bg-[#a8213e] transition-all shadow-[0_0_20px_rgba(203,41,87,0.4)]"
            >
              Access System Console →
            </Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-[#1a1a1a] px-6 py-6 bg-[#030303]">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-5 w-5 items-center justify-center rounded bg-[#CB2957]">
              <svg width="10" height="10" viewBox="0 0 14 14" fill="none">
                <rect x="0" y="3" width="9" height="8" rx="1.2" fill="white"/>
                <path d="M9 5.5l4.5-2.5v8l-4.5-2.5V5.5z" fill="white"/>
              </svg>
            </div>
            <span className="text-xs font-bold text-white">SENTINELRAG</span>
          </div>
          <div className="text-xs font-medium text-[#888888]">
            YOLO11 · Gemini 2.5 Flash · Supabase pgvector
          </div>
        </div>
      </footer>
    </div>
  )
}
