import { useEffect, useState } from 'react'
import { CalendarClock, ExternalLink, Trash2, Users } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { api } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'

interface CalendarEvent {
  id: string
  title: string
  start_time: string
  end_time: string
  html_link: string | null
  attendees: string[]
}

export default function EventList() {
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<CalendarEvent | null>(null)
  const [tab, setTab] = useState<'upcoming' | 'past'>('upcoming')

  async function handleDelete() {
    if (!deleteTarget) return
    const target = deleteTarget
    setDeleteTarget(null)
    setEvents((prev) => prev.filter((e) => e.id !== target.id))
    try {
      await api.delete(`/calendar/events/${target.id}`)
    } catch {
      setEvents((prev) => [...prev])
    }
  }

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const res = await api.get<{ data: CalendarEvent[] }>('/calendar/events')
        if (cancelled) return
        setEvents(res.data.data)
      } catch {
        if (!cancelled) setError('Failed to load calendar events')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const now = Date.now()
  const visibleEvents = events
    .filter((e) =>
      tab === 'upcoming' ? new Date(e.start_time).getTime() >= now : new Date(e.start_time).getTime() < now,
    )
    .sort((a, b) =>
      tab === 'upcoming'
        ? new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
        : new Date(b.start_time).getTime() - new Date(a.start_time).getTime(),
    )

  return (
    <Card>
      <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <CardTitle className="flex items-center gap-2">
          <CalendarClock className="size-4" /> {tab === 'upcoming' ? 'Upcoming events' : 'Past events'}
        </CardTitle>
        <Tabs value={tab} onValueChange={(value) => setTab(value as 'upcoming' | 'past')}>
          <TabsList>
            <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
            <TabsTrigger value="past">Past</TabsTrigger>
          </TabsList>
        </Tabs>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {loading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-2/3" />
          </div>
        )}

        {!loading && error && <p className="text-sm text-destructive">{error}</p>}

        {!loading && !error && visibleEvents.length === 0 && (
          <p className="text-sm text-muted-foreground">
            {tab === 'upcoming' ? 'No upcoming events.' : 'No past events.'}
          </p>
        )}

        {!loading && !error && visibleEvents.length > 0 && (
          <ul className="flex flex-col gap-4">
            {visibleEvents.map((event) => (
              <li key={event.id} className="group flex flex-col gap-1.5 border-b pb-4 last:border-b-0 last:pb-0">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-sm font-medium">{event.title}</span>
                  <div className="flex items-center gap-2">
                    {event.html_link && (
                      <a
                        href={event.html_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex shrink-0 items-center gap-1 text-xs text-primary underline-offset-4 hover:underline"
                      >
                        Open in Google Calendar <ExternalLink className="size-3" />
                      </a>
                    )}
                    <button
                      className="opacity-0 transition-opacity group-hover:opacity-100"
                      onClick={() => setDeleteTarget(event)}
                      aria-label={`Delete "${event.title}"`}
                    >
                      <Trash2 className="size-3.5 text-muted-foreground hover:text-destructive" />
                    </button>
                  </div>
                </div>
                <span className="text-xs text-muted-foreground">
                  {formatDateTime(event.start_time)} – {formatDateTime(event.end_time)}
                </span>
                {event.attendees.length > 0 && (
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    <Users className="size-3.5 text-muted-foreground" />
                    {event.attendees.map((email) => (
                      <Badge key={email} variant="secondary">
                        {email}
                      </Badge>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>

      <Dialog open={!!deleteTarget} onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete event</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &ldquo;{deleteTarget?.title}&rdquo;? This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={() => void handleDelete()}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
