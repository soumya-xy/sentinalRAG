import { useState, type ChangeEvent, type DragEvent, type FormEvent } from 'react'

import { Button } from '../../components/Button.tsx'
import { EmptyState } from '../../components/EmptyState.tsx'
import { ErrorBanner } from '../../components/ErrorBanner.tsx'
import { Field } from '../../components/Field.tsx'
import { Input } from '../../components/Input.tsx'
import { StatusDot, statusToTone } from '../../components/StatusDot.tsx'
import { api, ApiError } from '../../lib/api/index.ts'
import { formatBytes } from '../../lib/format.ts'
import {
  currentStageHeadline,
  stageExplanation,
  stageToneClass,
} from '../../lib/pipelineCopy.ts'
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
  const [retrying, setRetrying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [duplicateNotice, setDuplicateNotice] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)

  function takeFile(next: File | null) {
    setFile(next)
    setError(null)
    setDuplicateNotice(null)
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
    setDuplicateNotice(null)
    try {
      const record = await api.uploadVideo(file, cameraId.trim() || 'cam-01')
      setFile(null)
      if (record.duplicate) {
        setDuplicateNotice(
          `This file was already processed. Reusing ${record.video_id} — pipeline was not run again.`,
        )
      }
      await onUploaded(record)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  async function onRetry() {
    if (!video || retrying) return
    setRetrying(true)
    setError(null)
    try {
      const record = await api.retryIngest(video.video_id)
      await onUploaded(record)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Retry failed')
    } finally {
      setRetrying(false)
    }
  }

  const isProcessing = video && (status?.status === 'processing' || status?.status === 'uploaded')
  const isReady = status?.status === 'ready'
  const isFailed = status?.status === 'failed'

  return (
    <div className="max-w-2xl px-6 py-6 font-sans">

      {/* Section header */}
      <div className="mb-5 space-y-1">
        <div className="text-xs font-bold uppercase tracking-wider text-[#CB2957]">Footage Ingestion</div>
        <h1 className="text-2xl font-bold text-white">Upload CCTV Recording</h1>
        <p className="text-xs sm:text-sm text-[#CCCCCC] leading-relaxed">
          This is a one-time batch. The file is stored, stills are sampled, YOLO11 labels objects,
          Gemini writes a caption per event, and those sentences are embedded into Supabase pgvector.
        </p>
      </div>

      {/* Upload form */}
      <form onSubmit={onSubmit} className="space-y-4">
        {error ? <ErrorBanner message={error} /> : null}
        {duplicateNotice ? (
          <div className="rounded-md border border-[#22c55e]/30 bg-[#22c55e]/10 px-3.5 py-2.5 text-xs text-[#DDDDDD] leading-relaxed">
            <span className="font-semibold text-[#22c55e] uppercase tracking-wider">Duplicate </span>
            {duplicateNotice}
          </div>
        ) : null}

        {/* Drop zone */}
        <label
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          className={[
            'group relative flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 transition-all duration-200',
            dragOver
              ? 'border-[#CB2957] bg-[#CB2957]/5'
              : 'border-[#2c2c2c] bg-[#050505] hover:border-[#CB2957]/50 hover:bg-[#CB2957]/3',
          ].join(' ')}
        >
          <div className={`mb-3 flex h-11 w-11 items-center justify-center rounded-lg border transition-colors ${dragOver ? 'border-[#CB2957]/60 bg-[#CB2957]/10' : 'border-[#262626] bg-[#0a0a0a] group-hover:border-[#CB2957]/40'}`}>
            <svg width="20" height="20" viewBox="0 0 22 22" fill="none" className={`transition-colors ${dragOver ? 'text-[#CB2957]' : 'text-[#CCCCCC] group-hover:text-white'}`}>
              <rect x="2" y="6" width="14" height="12" rx="1.5" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M16 10l5.5-3.5v11L16 14" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
              <path d="M9 13V7m-2 2l2-2 2 2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>

          {file ? (
            <div className="text-center">
              <div className="font-mono text-xs sm:text-sm text-[#EEEEEE] font-semibold">{file.name}</div>
              <div className="mt-1 font-mono text-xs text-[#CB2957]">{formatBytes(file.size)}</div>
              <div className="mt-1.5 font-sans text-xs text-[#AAAAAA]">Click to change file</div>
            </div>
          ) : (
            <div className="text-center space-y-1">
              <div className="text-xs sm:text-sm font-medium text-[#EEEEEE]">
                {dragOver ? 'Drop footage here' : 'Drag & drop CCTV recording or click to browse'}
              </div>
              <div className="font-mono text-[10px] text-[#AAAAAA] uppercase tracking-wider">
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
            className="max-w-xs font-mono text-xs"
          />
        </Field>

        <Button type="submit" disabled={uploading || !file} size="md" className="font-semibold text-xs">
          {uploading ? (
            <>
              <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
              Uploading & Processing…
            </>
          ) : (
            'Begin Ingestion Pipeline'
          )}
        </Button>
      </form>

      {/* Active video status */}
      {video ? (
        <section className="mt-10 space-y-3">
          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="h-px flex-1 bg-[#1f1f1f]" />
            <span className="font-mono text-[10px] uppercase tracking-wider text-[#AAAAAA]">Active Recording Stream</span>
            <div className="h-px flex-1 bg-[#1f1f1f]" />
          </div>

          <div className="rounded-lg border border-[#222222] bg-[#080808] p-4 space-y-3">
            {/* File info */}
            <div className="flex items-start justify-between">
              <div>
                <div className="font-mono text-xs sm:text-sm font-semibold text-[#EEEEEE]">{video.original_filename}</div>
                <div className="mt-0.5 font-mono text-xs text-[#AAAAAA]">
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
            <div className="font-mono text-[10px] text-[#AAAAAA] space-x-2 bg-[#111111] px-2.5 py-1 rounded border border-[#222222] inline-block">
              <span>{video.video_id}</span>
              <span>·</span>
              <span>{video.camera_id}</span>
              {video.content_hash ? (
                <>
                  <span>·</span>
                  <span title={video.content_hash}>sha256 {video.content_hash.slice(0, 12)}</span>
                </>
              ) : null}
            </div>

            {/* Error */}
            {status?.error ? <ErrorBanner message={status.error} /> : null}

            {isFailed && (
              <div className="flex items-center justify-between gap-3 rounded-md border border-[#ef4444]/30 bg-[#ef4444]/10 px-3.5 py-2.5">
                <span className="font-sans text-xs text-[#ef4444]">
                  Ingest failed — file stored. You can retry pipeline without re-uploading.
                </span>
                <Button type="button" variant="ghost" size="sm" disabled={retrying} onClick={() => void onRetry()}>
                  {retrying ? 'Retrying…' : 'Retry pipeline'}
                </Button>
              </div>
            )}

            {status && (
              <p className="text-xs text-[#CCCCCC] leading-relaxed">
                {currentStageHeadline(status.stages, status.current_stage, status.status)}
              </p>
            )}

            {/* Pipeline stages */}
            {status?.stages && status.stages.length > 0 && (
              <div className="space-y-0 border border-[#222222] rounded-md overflow-hidden">
                {status.stages.map((stage, i) => (
                  <div
                    key={stage.key}
                    className={`flex items-start gap-3.5 px-3.5 py-2.5 ${i > 0 ? 'border-t border-[#181818]' : ''} ${stage.state === 'running' ? 'bg-[#CB2957]/10' : 'bg-[#030303]'}`}
                  >
                    <span className="font-mono text-[10px] text-[#888888] w-4 shrink-0 pt-0.5">{String(i + 1).padStart(2, '0')}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className={`text-xs font-semibold ${stageToneClass(stage.state)}`}>
                          {stage.label}
                        </span>
                        <StatusDot tone={stageTone(stage.state)} label={stage.state} />
                      </div>
                      <p className="mt-0.5 text-xs text-[#AAAAAA] leading-relaxed">
                        {stageExplanation(stage)}
                      </p>
                      {stage.state === 'running' && (
                        <div className="mt-2 h-1 w-full bg-[#181818] rounded-full overflow-hidden">
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
                <span className="font-sans text-xs font-semibold uppercase tracking-wider text-[#AAAAAA]">Overall Progress</span>
                <span className="font-mono text-xs font-bold text-[#CB2957]">{status.progress.toFixed(0)}%</span>
              </div>
            )}

            {isReady && (
              <div className="rounded-md border border-[#22c55e]/30 bg-[#22c55e]/10 px-3.5 py-2.5 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e]" />
                  <span className="font-sans text-xs font-semibold text-[#22c55e] uppercase tracking-wider">
                    Index Ready
                  </span>
                </div>
                <p className="text-xs text-[#DDDDDD] leading-relaxed">
                  Open Intelligence Query to start asking questions grounded to stored captions and visual evidence frames.
                </p>
              </div>
            )}
          </div>
        </section>
      ) : (
        <div className="mt-8">
          <EmptyState
            title="No recordings ingested"
            body="Choose a recorded CCTV file above. You will see each stage explain itself: store, sample, detect, group, caption, then index."
          />
        </div>
      )}
    </div>
  )
}
