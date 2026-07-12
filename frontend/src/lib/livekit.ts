import { api } from '@/lib/api'

export interface LiveKitTokenResponse {
  token: string
  url: string
  room: string
}

export async function fetchLiveKitToken(): Promise<LiveKitTokenResponse> {
  const res = await api.post<{ data: LiveKitTokenResponse }>('/livekit/token')
  return res.data.data
}
