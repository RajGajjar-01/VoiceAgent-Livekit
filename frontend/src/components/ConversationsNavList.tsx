import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
} from '@/components/ui/sidebar'
import { api } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'

interface Conversation {
  id: string
  room: string
  started_at: string
  ended_at: string | null
}

export default function ConversationsNavList() {
  const { conversationId } = useParams()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
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
  }, [])

  return (
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
              </SidebarMenuItem>
            ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
