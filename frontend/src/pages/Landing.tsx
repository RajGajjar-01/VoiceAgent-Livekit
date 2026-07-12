import GoogleIcon from '@/components/icons/GoogleIcon'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function LandingPage() {
  const apiUrl = import.meta.env.VITE_API_URL ?? ''
  const params = new URLSearchParams(window.location.search)
  const error = params.get('error')

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 bg-background p-6">
      <div className="text-center">
        <h1 className="font-heading text-2xl leading-tight font-semibold tracking-tight text-balance">
          Voice Agent
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Manage tasks, book calendar events, and pick up where you left off — all by voice.
        </p>
      </div>

      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>Continue with your Google account to get started.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className="text-sm text-destructive">
              {error === 'consent_denied' ? 'Google sign-in was cancelled.' : 'Sign-in failed. Please try again.'}
            </p>
          )}
          <Button variant="outline" className="w-full gap-2" render={<a href={`${apiUrl}/api/v1/auth/google/login`} />}>
            <GoogleIcon className="size-4" />
            Continue with Google
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
