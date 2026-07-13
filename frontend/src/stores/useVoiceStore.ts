import { Room, RoomEvent, type Participant } from 'livekit-client'
import { toast } from 'sonner'
import { create } from 'zustand'
import { fetchLiveKitToken } from '@/lib/livekit'

export interface TranscriptEntry {
  id: string
  speaker: 'user' | 'agent'
  text: string
  final: boolean
}

type VoiceStatus = 'idle' | 'connecting' | 'connected' | 'error'

interface VoiceState {
  status: VoiceStatus
  room: Room | null
  muted: boolean
  transcript: TranscriptEntry[]
  agentSpeaking: boolean
  error: string | null
}

interface VoiceActions {
  connect: () => Promise<void>
  disconnect: () => Promise<void>
  toggleMute: () => Promise<void>
}

export const useVoiceStore = create<VoiceState & VoiceActions>((set, get) => ({
  status: 'idle',
  room: null,
  muted: false,
  transcript: [],
  agentSpeaking: false,
  error: null,

  connect: async () => {
    if (get().status === 'connecting' || get().status === 'connected') return
    set({ status: 'connecting', error: null, transcript: [] })

    try {
      const { token, url } = await fetchLiveKitToken()
      const room = new Room()

      room.on(RoomEvent.Disconnected, () => {
        set({ status: 'idle', room: null, agentSpeaking: false })
      })

      // STT segments arrive as interim updates that get refined until
      // final=true, all sharing the same id — dedupe by id so the
      // transcript updates a bubble in place instead of appending
      // duplicates for every partial transcription.
      room.on(RoomEvent.TranscriptionReceived, (segments, participant) => {
        const speaker: 'user' | 'agent' = participant?.isLocal ? 'user' : 'agent'
        set((state) => {
          const byId = new Map(state.transcript.map((entry) => [entry.id, entry]))
          for (const seg of segments) {
            byId.set(seg.id, { id: seg.id, speaker, text: seg.text, final: seg.final })
          }
          return { transcript: Array.from(byId.values()) }
        })
      })

      room.on(RoomEvent.ActiveSpeakersChanged, (speakers: Participant[]) => {
        set({ agentSpeaking: speakers.some((p) => !p.isLocal) })
      })

      // The worker runs as a separate LiveKit agent process with no HTTP
      // channel back to the browser, so it reports things like "the LLM
      // rate limit was exhausted" over the room's data channel instead.
      room.on(RoomEvent.DataReceived, (payload, _participant, _kind, topic) => {
        if (topic !== 'agent-error') return
        try {
          const { message } = JSON.parse(new TextDecoder().decode(payload)) as { message?: string }
          if (message) toast.error(message)
        } catch {
          // Malformed payload — nothing sensible to show the user.
        }
      })

      await room.connect(url, token)
      await room.localParticipant.setMicrophoneEnabled(true)

      set({ status: 'connected', room, muted: false })
    } catch (err) {
      set({ status: 'error', error: err instanceof Error ? err.message : 'Failed to connect' })
    }
  },

  disconnect: async () => {
    const { room } = get()
    if (room) await room.disconnect()
    set({ status: 'idle', room: null, muted: false, agentSpeaking: false })
  },

  toggleMute: async () => {
    const { room, muted } = get()
    if (!room) return
    await room.localParticipant.setMicrophoneEnabled(muted)
    set({ muted: !muted })
  },
}))
