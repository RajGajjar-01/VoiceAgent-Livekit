import { useState } from 'react'
import { ChevronsUpDown, LogOut, User as UserIcon } from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from '@/components/ui/sidebar'
import { useAuth } from '@/hooks/useAuth'

function initials(name: string | null, email: string): string {
  const source = name?.trim() || email
  return source.slice(0, 2).toUpperCase()
}

export default function UserMenu() {
  const { user, logout } = useAuth()
  const [profileOpen, setProfileOpen] = useState(false)

  if (!user) return null

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <SidebarMenuButton
                  size="lg"
                  className="data-popup-open:bg-sidebar-accent data-popup-open:text-sidebar-accent-foreground"
                />
              }
            >
              <Avatar className="size-8 rounded-lg">
                <AvatarImage src={user.avatar_url ?? undefined} alt={user.name ?? user.email} />
                <AvatarFallback className="rounded-lg">{initials(user.name, user.email)}</AvatarFallback>
              </Avatar>
              <div className="grid flex-1 text-left text-sm leading-tight group-data-[collapsible=icon]:hidden">
                <span className="truncate font-medium">{user.name ?? 'Unnamed'}</span>
                <span className="truncate text-xs text-muted-foreground">{user.email}</span>
              </div>
              <ChevronsUpDown className="ml-auto size-4 group-data-[collapsible=icon]:hidden" />
            </DropdownMenuTrigger>
            <DropdownMenuContent side="top" align="start" className="w-(--sidebar-width) min-w-56">
              <DropdownMenuItem onClick={() => setProfileOpen(true)}>
                <UserIcon /> Profile
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem variant="destructive" onClick={() => void logout()}>
                <LogOut /> Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>

      <Dialog open={profileOpen} onOpenChange={setProfileOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Profile</DialogTitle>
            <DialogDescription>Your account details.</DialogDescription>
          </DialogHeader>
          <div className="flex items-center gap-4">
            <Avatar size="lg">
              <AvatarImage src={user.avatar_url ?? undefined} alt={user.name ?? user.email} />
              <AvatarFallback>{initials(user.name, user.email)}</AvatarFallback>
            </Avatar>
            <div className="flex flex-col">
              <span className="text-sm font-medium">{user.name ?? 'Unnamed'}</span>
              <span className="text-sm text-muted-foreground">{user.email}</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
