import { useState, type ChangeEvent, type DragEvent, type FormEvent } from 'react'

import { Button } from '../../components/Button.tsx'
import { EmptyState } from '../../components/EmptyState.tsx'
import { ErrorBanner } from '../../components/ErrorBanner.tsx'
import { Field } from '../../components/Field.tsx'
import { Input } from '../../components/Input.tsx'
import { StatusDot } from '../../components/StatusDot.tsx'
import { api, ApiError } from '../../lib/api/index.ts'
import { formatBytes } from '../../lib/format.ts'
import type { PipelineStage, VideoRecord, VideoStatusResponse } from '../../types/api.ts'

function stageTone(state: PipelineStage['state']): 'sage' | 'warning' | 'critical' | 'muted' {
  if (state === 'complete') return 'sage'
  if (state === 'running') return 'warning'
  if (state === 'failed') return 'critical'
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

  function onFile(event: ChangeEvent<HTMLInputElement>) {
    takeFile(event.target.files?.[0] ?? null)
  }

  function onDrop(event: DragEvent) {
    event.preventDefault()
    setDragOver(false)
    takeFile(event.dataTransfer.files?.[0] ?? null)
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!file) {
      setError('Select a recorded video file.')
      return
    }
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

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-medium">Ingest</h1>
      <p className="mt-2 max-w-prose text-sm text-muted">
        Phase 1 accepts a single recorded video. Processing is batch: sample, detect with
        YOLO11, caption with Gemini, then index in Supabase pgvector. Query stays closed until the
        last stage completes.
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        {error ? <ErrorBanner message={error} /> : null}

        <label
          onDragOver={(event) => {
            event.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          className={`block cursor-pointer border bg-surface px-4 py-8 ${
            dragOver ? 'border-sage' : 'border-border'
          }`}
        >
          <div className="text-sm">Select a recorded video</div>
          <div className="mt-1 font-mono text-xs text-muted">mp4  mov  webm  mkv  avi</div>
          {file ? (
            <div className="mt-3 font-mono text-sm">
              {file.name}  {formatBytes(file.size)}
            </div>
          ) : (
            <div className="mt-3 text-sm text-muted">No file selected</div>
          )}
          <input type="file" accept="video/*" className="sr-only" onChange={onFile} />
        </label>

        <Field label="Camera ID" hint="Required in the schema even for a single-video Phase 1.">
          <Input
            value={cameraId}
            onChange={(event) => setCameraId(event.target.value)}
            className="font-mono max-w-xs"
          />
        </Field>

        <Button type="submit" disabled={uploading}>
          {uploading ? 'Uploading…' : 'Start batch processing'}
        </Button>
      </form>

      {!video ? (
        <div className="mt-12">
          <EmptyState
            title="Nothing ingested yet"
            body="Choose a recorded CCTV file. The backend will sample frames, run YOLO11, caption events, and index them for questions."
          />
        </div>
      ) : (
        <section className="mt-12">
          <div className="text-sm text-muted">Active video</div>
          <div className="mt-1 font-mono text-sm">
            {video.original_filename}  {formatBytes(video.size_bytes)}
          </div>
          <div className="mt-1 font-mono text-xs text-muted">
            {video.video_id}  {video.camera_id}
          </div>

          {status?.error ? (
            <div className="mt-4">
              <ErrorBanner message={status.error} />
            </div>
          ) : null}

          <ol className="mt-6 divide-y divide-border border-y border-border">
            {(status?.stages ?? []).map((stage, index) => (
              <li key={stage.key} className="grid grid-cols-[3rem_1fr_7rem] items-center gap-4 py-3">
                <span className="font-mono text-sm text-muted">{String(index + 1).padStart(2, '0')}</span>
                <div>
                  <div>{stage.label}</div>
                  {stage.state === 'running' ? (
                    <div className="mt-2 h-1 w-full max-w-xs bg-border">
                      <div
                        className="h-1 bg-warning transition-[width] duration-300"
                        style={{ width: `${stage.progress}%` }}
                      />
                    </div>
                  ) : null}
                </div>
                <span className="font-mono text-xs text-muted">
                  <StatusDot tone={stageTone(stage.state)} label={stage.state} />
                </span>
              </li>
            ))}
          </ol>

          {status ? (
            <div className="mt-4 font-mono text-xs text-muted">
              overall {status.progress.toFixed(0)}%
              {status.caption_mode ? `  caption=${status.caption_mode}` : ''}
            </div>
          ) : null}
        </section>
      )}
    </div>
  )
}
