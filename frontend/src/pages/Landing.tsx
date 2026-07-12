import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function LandingPage() {
  const apiUrl = import.meta.env.VITE_API_URL ?? ''
  const params = new URLSearchParams(window.location.search)
  const error = params.get('error')

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className="text-sm text-destructive">
              {error === 'consent_denied' ? 'Google sign-in was cancelled.' : 'Sign-in failed. Please try again.'}
            </p>
          )}
          <Button className="w-full" render={<a href={`${apiUrl}/api/v1/auth/google/login`} />}>
            Continue with Google
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
