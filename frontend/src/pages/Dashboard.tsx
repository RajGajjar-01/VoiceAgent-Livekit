import { useAuth } from '@/hooks/useAuth'

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">
        Welcome{user?.name ? `, ${user.name}` : ''}
      </h1>
      <p className="text-sm text-muted-foreground">Here&apos;s what&apos;s happening.</p>
    </div>
  )
}
