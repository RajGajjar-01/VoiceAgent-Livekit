import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
} from '@/components/ui/sidebar'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'
import { useVoiceStore } from '@/stores/useVoiceStore'

interface Conversation {
  id: string
  room: string
  started_at: string
  ended_at: string | null
}

export default function ConversationsNavList() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const status = useVoiceStore((s) => s.status)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [deleteTarget, setDeleteTarget] = useState<Conversation | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    // Refetch whenever a call starts or ends, not just on mount — the
    // sidebar stays mounted across route navigation, so the initial fetch
    // alone would leave the list stale for the rest of the session.
    if (status === 'connecting') return
    let cancelled = false
    void (async () => {
      try {
        const res = await api.get<{ data: Conversation[] }>('/conversations')
        if (!cancelled) setConversations(res.data.data)
      } catch {
        // sidebar recents are non-critical; fail silently rather than blocking nav
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [status])

  const handleDeleteClick = (e: React.MouseEvent, conv: Conversation) => {
    e.preventDefault()
    e.stopPropagation()
    setDeleteTarget(conv)
  }

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await api.delete(`/conversations/${deleteTarget.id}`)
      setConversations((prev) => prev.filter((c) => c.id !== deleteTarget.id))
      // If the user was viewing the deleted conversation, send them home
      if (conversationId === deleteTarget.id) {
        navigate('/')
      }
      setDeleteTarget(null)
    } catch {
      // fail silently – list remains unchanged
    } finally {
      setDeleting(false)
    }
  }

  return (
    <>
      <SidebarGroup className="group-data-[collapsible=icon]:hidden">
        <SidebarGroupLabel>Conversations</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {loading && (
              <>
                <SidebarMenuSkeleton />
                <SidebarMenuSkeleton />
              </>
            )}
            {!loading && conversations.length === 0 && (
              <p className="px-2 py-1.5 text-xs text-sidebar-foreground/60">No conversations yet.</p>
            )}
            {!loading &&
              conversations.map((c) => (
                <SidebarMenuItem key={c.id}>
                  <SidebarMenuButton
                    isActive={conversationId === c.id}
                    size="sm"
                    render={<Link to={`/conversations/${c.id}`} />}
                  >
                    <span>{formatDateTime(c.started_at)}</span>
                  </SidebarMenuButton>

                  {/* Trash icon — visible only on row hover */}
                  <SidebarMenuAction
                    showOnHover
                    onClick={(e) => handleDeleteClick(e, c)}
                    aria-label="Delete conversation"
                    title="Delete conversation"
                    className="text-sidebar-foreground/50 hover:text-destructive hover:bg-destructive/10"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                      <path d="M10 11v6" />
                      <path d="M14 11v6" />
                      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                    </svg>
                  </SidebarMenuAction>
                </SidebarMenuItem>
              ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      {/* Shadcn confirmation dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={(open) => { if (!open && !deleting) setDeleteTarget(null) }}>
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <div className="flex items-center gap-2.5">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-destructive/15 text-destructive">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                  <path d="M10 11v6" />
                  <path d="M14 11v6" />
                  <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                </svg>
              </span>
              <DialogTitle>Delete Conversation</DialogTitle>
            </div>
            <DialogDescription>
              This will permanently delete the conversation from{' '}
              <span className="font-medium text-foreground">
                {deleteTarget ? formatDateTime(deleteTarget.started_at) : ''}
              </span>
              . This action cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button
              variant="outline"
              disabled={deleting}
              onClick={() => setDeleteTarget(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={deleting}
              onClick={handleConfirmDelete}
            >
              {deleting && (
                <svg
                  className="mr-1.5 h-3.5 w-3.5 animate-spin"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              )}
              {deleting ? 'Deleting…' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
