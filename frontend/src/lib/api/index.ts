import type {
  AuthResponse,
  EventListResponse,
  HealthResponse,
  QueryRequest,
  QueryResponse,
  User,
  VideoListResponse,
  VideoRecord,
  VideoStatusResponse,
} from '../../types/api.ts'
import { request } from './client.ts'

export { API_BASE, ApiError, resolveMediaUrl } from './client.ts'

export const api = {
  health: () => request<HealthResponse>('/api/health'),

  register: (body: { email: string; password: string; display_name?: string }) =>
    request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  login: (body: { email: string; password: string }) =>
    request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  logout: () => request<{ ok: boolean }>('/api/auth/logout', { method: 'POST' }),

  me: () => request<User>('/api/auth/me'),

  listVideos: () => request<VideoListResponse>('/api/videos'),

  uploadVideo: (file: File, cameraId: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('camera_id', cameraId)
    return request<VideoRecord>('/api/videos', { method: 'POST', body: form })
  },

  getVideo: (videoId: string) => request<VideoRecord>(`/api/videos/${videoId}`),

  getVideoStatus: (videoId: string) =>
    request<VideoStatusResponse>(`/api/videos/${videoId}/status`),

  listEvents: (videoId: string) => request<EventListResponse>(`/api/videos/${videoId}/events`),

  query: (body: QueryRequest) =>
    request<QueryResponse>('/api/query', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
