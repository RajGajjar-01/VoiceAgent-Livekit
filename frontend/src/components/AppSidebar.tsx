import { CalendarDays, ListTodo, Plus } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router'
import ConversationsNavList from '@/components/ConversationsNavList'
import UserMenu from '@/components/UserMenu'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { useVoiceStore } from '@/stores/useVoiceStore'

const NAV_ITEMS = [
  { to: '/tasks', label: 'Tasks', icon: ListTodo },
  { to: '/events', label: 'Events', icon: CalendarDays },
]

export default function AppSidebar() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const connect = useVoiceStore((s) => s.connect)

  function handleNewConversation() {
    void navigate('/voice')
    void connect()
  }

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="flex items-center justify-between gap-2 px-2 py-1.5 group-data-[collapsible=icon]:justify-center">
          <span className="font-heading text-sm font-semibold group-data-[collapsible=icon]:hidden">
            Voice Agent
          </span>
          <SidebarTrigger />
        </div>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton tooltip="New conversation" onClick={handleNewConversation}>
              <Plus />
              <span>New conversation</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
                <SidebarMenuItem key={to}>
                  <SidebarMenuButton isActive={pathname === to} tooltip={label} render={<Link to={to} />}>
                    <Icon />
                    <span>{label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <ConversationsNavList />
      </SidebarContent>
      <SidebarFooter>
        <UserMenu />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
