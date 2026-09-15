export interface User {
  user_id: string
  email: string
  display_name: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface BoundingBox {
  x: number
  y: number
  w: number
  h: number
  frame_timestamp: string
}

export interface EventRecord {
  event_id: string
  video_id: string
  camera_id: string
  start_timestamp: string
  end_timestamp: string
  caption: string
  detected_classes: string[]
  bounding_boxes: BoundingBox[]
  thumbnail_path: string
  confidence_score: number
  thumbnail_url?: string | null
  caption_source?: string | null
}

export interface EventListResponse {
  video_id: string
  camera_id: string
  count: number
  events: EventRecord[]
}

export type VideoStatus = 'uploaded' | 'processing' | 'ready' | 'failed'
export type StageState = 'pending' | 'running' | 'complete' | 'failed'

export interface PipelineStage {
  key: string
  label: string
  state: StageState
  progress: number
}

export interface VideoRecord {
  video_id: string
  camera_id: string
  filename: string
  original_filename: string
  status: VideoStatus
  duration_seconds: number | null
  created_at: string
  size_bytes: number
}

export interface VideoListResponse {
  videos: VideoRecord[]
}

export interface VideoStatusResponse {
  video_id: string
  status: VideoStatus
  current_stage: string | null
  progress: number
  stages: PipelineStage[]
  error: string | null
  caption_mode?: string | null
}

export interface QueryRequest {
  question: string
  video_id: string
}

export interface Citation {
  event_id: string
  video_id: string
  camera_id: string
  start_timestamp: string
  end_timestamp: string
  thumbnail_path: string
  thumbnail_url?: string | null
  confidence_score: number
  caption: string
}

export interface QueryResponse {
  answer: string
  citations: Citation[]
  retrieved_event_ids: string[]
  video_id: string
  camera_id: string
}

export interface HealthResponse {
  status: 'ok'
  service: string
  env: string
  phase: string
}
