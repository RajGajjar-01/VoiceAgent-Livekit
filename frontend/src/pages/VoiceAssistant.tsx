import { useEffect, useRef } from 'react'
import { RoomAudioRenderer } from '@livekit/components-react'
import { Mic, MicOff, Phone, PhoneOff } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
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
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      {room && <RoomAudioRenderer room={room} />}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Voice Assistant</h1>
        <p className="text-sm text-muted-foreground">Ask it to manage your tasks or book a calendar event.</p>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Badge variant={status === 'connected' ? 'default' : 'secondary'}>{STATUS_LABEL[status]}</Badge>
            {agentSpeaking && <span className="text-xs text-muted-foreground">Agent is speaking…</span>}
          </CardTitle>
          <div className="flex items-center gap-2">
            {status === 'connected' && (
              <Button
                variant="outline"
                size="icon"
                onClick={() => void toggleMute()}
                aria-label={muted ? 'Unmute microphone' : 'Mute microphone'}
              >
                {muted ? <MicOff className="size-4" /> : <Mic className="size-4" />}
              </Button>
            )}
            {status === 'connected' ? (
              <Button variant="destructive" size="sm" onClick={() => void disconnect()}>
                <PhoneOff className="size-4" /> End call
              </Button>
            ) : (
              <Button size="sm" onClick={() => void connect()} disabled={status === 'connecting'}>
                <Phone className="size-4" /> {status === 'connecting' ? 'Connecting…' : 'Start talking'}
              </Button>
            )}
          </div>
        </CardHeader>
        <Separator />
        <CardContent className="flex h-96 flex-col gap-3 overflow-y-auto pt-4">
          {error && <p className="text-sm text-destructive">{error}</p>}
          {transcript.length === 0 && status !== 'connecting' && !error && (
            <p className="text-sm text-muted-foreground">Transcript will appear here once you start talking.</p>
          )}
          {transcript.map((entry) => (
            <div
              key={entry.id}
              className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                entry.speaker === 'user' ? 'self-end bg-primary text-primary-foreground' : 'self-start bg-muted'
              } ${entry.final ? '' : 'opacity-60'}`}
            >
              {entry.text}
            </div>
          ))}
          <div ref={transcriptEndRef} />
        </CardContent>
      </Card>
    </div>
  )
}
