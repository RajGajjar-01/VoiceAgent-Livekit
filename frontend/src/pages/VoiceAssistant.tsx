import { useEffect, useRef } from 'react'
import { RoomAudioRenderer } from '@livekit/components-react'
import { Mic, MicOff, Phone, PhoneOff } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useVoiceStore } from '@/stores/useVoiceStore'

const STATUS_LABEL: Record<string, string> = {
  idle: 'Not connected',
  connecting: 'Connecting…',
  connected: 'Connected',
  error: 'Error',
}

export default function VoiceAssistantPage() {
  const { status, room, muted, transcript, agentSpeaking, error, connect, disconnect, toggleMute } = useVoiceStore()
  const transcriptEndRef = useRef<HTMLDivElement>(null)
  const isActive = status === 'connected' || status === 'connecting'

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript])

  useEffect(() => {
    // Leave the room if the user navigates away mid-call rather than
    // leaking a connected LiveKit session in the background.
    return () => {
      void useVoiceStore.getState().disconnect()
    }
  }, [])

  return (
    <div className="mx-auto flex h-full w-full max-w-2xl flex-col">
      {room && <RoomAudioRenderer room={room} />}

      {!isActive ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-6 text-center">
          <div className="flex flex-col items-center gap-2">
            <h1 className="font-heading text-2xl font-semibold tracking-tight">Start a conversation</h1>
            <p className="max-w-xs text-sm text-muted-foreground">
              Ask it to manage your tasks or book a calendar event.
            </p>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <button
            type="button"
            onClick={() => void connect()}
            className="flex size-20 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105 hover:bg-primary/90 active:scale-95"
            aria-label="Start talking"
          >
            <Phone className="size-7" />
          </button>
          <span className="text-sm font-medium text-muted-foreground">Start talking</span>
        </div>
      ) : (
        <div className="flex flex-1 flex-col gap-4">
          <div className="flex flex-1 flex-col gap-3 overflow-y-auto">
            {transcript.map((entry) => (
              <div
                key={entry.id}
                className={`max-w-[80%] animate-in slide-in-from-bottom-1 fade-in duration-300 rounded-lg px-3 py-2 text-sm ${
                  entry.speaker === 'user' ? 'self-end bg-primary text-primary-foreground' : 'self-start bg-muted'
                } ${entry.final ? '' : 'opacity-60'}`}
              >
                {entry.text}
              </div>
            ))}
            <div ref={transcriptEndRef} />
          </div>

          <div className="flex justify-center pb-2">
            <div className="flex items-center gap-3 rounded-full border bg-card px-4 py-2 shadow-lg">
              <Badge variant={status === 'connected' ? 'default' : 'secondary'}>{STATUS_LABEL[status]}</Badge>
              {agentSpeaking && <span className="text-xs text-muted-foreground">Agent is speaking…</span>}
              <div className="h-4 w-px bg-border" />
              {status === 'connected' && (
                <Button
                  variant="outline"
                  size="icon"
                  className="rounded-full"
                  onClick={() => void toggleMute()}
                  aria-label={muted ? 'Unmute microphone' : 'Mute microphone'}
                >
                  {muted ? <MicOff className="size-4" /> : <Mic className="size-4" />}
                </Button>
              )}
              <Button
                variant="destructive"
                size="icon"
                className="rounded-full"
                onClick={() => void disconnect()}
                aria-label="End call"
              >
                <PhoneOff className="size-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
