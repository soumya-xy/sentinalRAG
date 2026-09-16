import { useState, type ChangeEvent, type DragEvent, type FormEvent } from 'react'

import { Button } from '../../components/Button.tsx'
import { EmptyState } from '../../components/EmptyState.tsx'
import { ErrorBanner } from '../../components/ErrorBanner.tsx'
import { Field } from '../../components/Field.tsx'
import { Input } from '../../components/Input.tsx'
import { StatusDot, statusToTone } from '../../components/StatusDot.tsx'
import { api, ApiError } from '../../lib/api/index.ts'
import { formatBytes } from '../../lib/format.ts'
import type { PipelineStage, VideoRecord, VideoStatusResponse } from '../../types/api.ts'

function stageTone(state: PipelineStage['state']): 'success' | 'warning' | 'danger' | 'muted' {
  if (state === 'complete') return 'success'
  if (state === 'running') return 'warning'
  if (state === 'failed') return 'danger'
  return 'muted'
}

export function VideoTab({
  video,
  status,
  onUploaded,
}: {
  video: VideoRecord | null
  status: VideoStatusResponse | null
  onUploaded: (record: VideoRecord) => Promise<void>
}) {
  const [file, setFile] = useState<File | null>(null)
  const [cameraId, setCameraId] = useState('cam-01')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)

  function takeFile(next: File | null) {
    setFile(next)
    setError(null)
  }

  function onFile(e: ChangeEvent<HTMLInputElement>) {
    takeFile(e.target.files?.[0] ?? null)
  }

  function onDrop(e: DragEvent) {
    e.preventDefault()
    setDragOver(false)
    takeFile(e.dataTransfer.files?.[0] ?? null)
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!file) { setError('Select a recorded video file first.'); return }
    setUploading(true)
    setError(null)
    try {
      const record = await api.uploadVideo(file, cameraId.trim() || 'cam-01')
      setFile(null)
      await onUploaded(record)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const isProcessing = video && (status?.status === 'processing' || status?.status === 'uploaded')
  const isReady = status?.status === 'ready'

  return (
    <div className="max-w-2xl px-8 py-8">

      {/* Section header */}
      <div className="mb-6">
        <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-[#CB2957]">Footage Ingestion</div>
        <h1 className="text-2xl font-bold text-[#EEEEEE]">Upload CCTV Recording</h1>
        <p className="mt-2 text-sm text-[#AAAAAA] leading-relaxed">
          Upload any pre-recorded surveillance video. The pipeline will sample frames at 0.8s intervals,
          run YOLO11 detection, caption events with Gemini Vision, and index embeddings into Supabase pgvector.
        </p>
      </div>

      {/* Upload form */}
      <form onSubmit={onSubmit} className="space-y-5">
        {error ? <ErrorBanner message={error} /> : null}

        {/* Drop zone */}
        <label
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          className={[
            'group relative flex cursor-pointer flex-col items-center justify-center rounded-sm border-2 border-dashed px-8 py-14 transition-all duration-200',
            dragOver
              ? 'border-[#CB2957] bg-[#CB2957]/5'
              : 'border-[#222222] bg-[#050505] hover:border-[#CB2957]/50 hover:bg-[#CB2957]/3',
          ].join(' ')}
        >
          <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-sm border transition-colors ${dragOver ? 'border-[#CB2957]/60 bg-[#CB2957]/10' : 'border-[#222222] bg-[#0a0a0a] group-hover:border-[#CB2957]/40'}`}>
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none" className={`transition-colors ${dragOver ? 'text-[#CB2957]' : 'text-[#888888] group-hover:text-[#AAAAAA]'}`}>
              <rect x="2" y="6" width="14" height="12" rx="1.5" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M16 10l5.5-3.5v11L16 14" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
              <path d="M9 13V7m-2 2l2-2 2 2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>

          {file ? (
            <div className="text-center">
              <div className="font-mono text-sm text-[#DDDDDD]">{file.name}</div>
              <div className="mt-1 font-mono text-xs text-[#CB2957]">{formatBytes(file.size)}</div>
              <div className="mt-2 font-mono text-[10px] text-[#888888]">Click to change file</div>
            </div>
          ) : (
            <div className="text-center">
              <div className="text-sm text-[#888888]">
                {dragOver ? 'Drop footage here' : 'Drag & drop footage or click to browse'}
              </div>
              <div className="mt-2 font-mono text-[10px] text-[#888888] uppercase tracking-widest">
                MP4 · MOV · MKV · AVI · WEBM
              </div>
            </div>
          )}
          <input type="file" accept="video/*" className="sr-only" onChange={onFile} />
        </label>

        {/* Camera ID */}
        <Field label="Camera ID" hint="Identifier assigned to this footage stream. Used in query results.">
          <Input
            value={cameraId}
            onChange={(e) => setCameraId(e.target.value)}
            placeholder="cam-01"
            className="max-w-xs font-mono"
          />
        </Field>

        <Button type="submit" disabled={uploading || !file}>
          {uploading ? (
            <>
              <span className="h-1.5 w-1.5 rounded-full bg-white pulse-dot" />
              Uploading & Processing…
            </>
          ) : (
            'Begin Ingestion Pipeline'
          )}
        </Button>
      </form>

      {/* Active video status */}
      {video ? (
        <section className="mt-12 space-y-4">
          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="h-px flex-1 bg-[#1a1a1a]" />
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#777777]">Active Recording</span>
            <div className="h-px flex-1 bg-[#1a1a1a]" />
          </div>

          <div className="rounded-sm border border-[#1a1a1a] bg-[#050505] p-5 space-y-4">
            {/* File info */}
            <div className="flex items-start justify-between">
              <div>
                <div className="font-mono text-sm text-[#DDDDDD]">{video.original_filename}</div>
                <div className="mt-1 font-mono text-xs text-[#888888]">
                  {formatBytes(video.size_bytes)}
                  {video.duration_seconds ? ` · ${video.duration_seconds.toFixed(1)}s` : ''}
                </div>
              </div>
              <StatusDot
                tone={statusToTone(status?.status ?? video.status)}
                label={status?.status ?? video.status}
                pulse={!!isProcessing}
              />
            </div>

            {/* IDs */}
            <div className="font-mono text-[10px] text-[#777777] space-x-3">
              <span>{video.video_id}</span>
              <span>·</span>
              <span>{video.camera_id}</span>
            </div>

            {/* Error */}
            {status?.error ? <ErrorBanner message={status.error} /> : null}

            {/* Pipeline stages */}
            {status?.stages && status.stages.length > 0 && (
              <div className="space-y-0 border border-[#111111] rounded-sm overflow-hidden">
                {status.stages.map((stage, i) => (
                  <div
                    key={stage.key}
                    className={`flex items-center gap-4 px-4 py-3 ${i > 0 ? 'border-t border-[#111111]' : ''} ${stage.state === 'running' ? 'bg-[#CB2957]/5' : 'bg-[#030303]'}`}
                  >
                    <span className="font-mono text-[10px] text-[#777777] w-5 shrink-0">{String(i + 1).padStart(2, '0')}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className={`text-xs ${stage.state === 'running' ? 'text-[#DDDDDD]' : stage.state === 'complete' ? 'text-[#999999]' : 'text-[#777777]'}`}>
                          {stage.label}
                        </span>
                        <StatusDot tone={stageTone(stage.state)} label={stage.state} />
                      </div>
                      {stage.state === 'running' && (
                        <div className="mt-2 h-0.5 w-full bg-[#111111] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-[#CB2957] transition-all duration-500"
                            style={{ width: `${stage.progress}%` }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Overall progress */}
            {status && (
              <div className="flex items-center justify-between">
                <span className="font-mono text-[9px] uppercase tracking-widest text-[#777777]">Overall Progress</span>
                <span className="font-mono text-xs text-[#CB2957]">{status.progress.toFixed(0)}%</span>
              </div>
            )}

            {isReady && (
              <div className="flex items-center gap-2 rounded-sm border border-[#22c55e]/20 bg-[#22c55e]/5 px-4 py-3">
                <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e]" />
                <span className="font-mono text-xs text-[#22c55e] uppercase tracking-widest">
                  Index ready — query interface unlocked
                </span>
              </div>
            )}
          </div>
        </section>
      ) : (
        <div className="mt-12">
          <EmptyState
            title="No recordings ingested"
            body="Choose a recorded CCTV file above. The backend will sample frames, run YOLO11, caption events with Gemini Vision, and index them for natural-language queries."
          />
        </div>
      )}
    </div>
  )
}
