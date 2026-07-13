import { useEffect, useState } from 'react'
import { useParams } from 'react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { api } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'

interface ConversationMessage {
  id: string
  role: string
  content: string
  created_at: string
}

export default function ConversationTranscriptPage() {
  const { conversationId } = useParams()
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    void (async () => {
      try {
        const res = await api.get<{ data: ConversationMessage[] }>(`/conversations/${conversationId}/messages`)
        if (!cancelled) setMessages(res.data.data)
      } catch {
        if (!cancelled) setError('Failed to load this conversation.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [conversationId])

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Conversation</h1>
        {messages[0] && (
          <p className="text-sm text-muted-foreground">{formatDateTime(messages[0].created_at)}</p>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Transcript</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {loading && (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-6 w-2/3" />
              <Skeleton className="h-6 w-1/2" />
            </div>
          )}

          {!loading && error && <p className="text-sm text-destructive">{error}</p>}

          {!loading && !error && messages.length === 0 && (
            <p className="text-sm text-muted-foreground">No messages were recorded for this conversation.</p>
          )}

          {!loading &&
            !error &&
            messages.map((message) => (
              <div
                key={message.id}
                className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                  message.role === 'user' ? 'self-end bg-primary text-primary-foreground' : 'self-start bg-muted'
                }`}
              >
                {message.content}
              </div>
            ))}
        </CardContent>
      </Card>
    </div>
  )
}
