import { useState } from 'react'
import GoogleIcon from '@/components/icons/GoogleIcon'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'

const FEATURE_CARDS = [
  {
    number: '01',
    label: 'Tasks',
    labelClassName: 'text-blue-400',
    title: 'Keep every task in one place.',
    description:
      'Ask the assistant to add, complete, or review your to-dos. Hands-free, whenever they come to mind.',
    tags: ['TASK TRACKING', 'VOICE ADD', 'QUICK COMPLETE'],
  },
  {
    number: '02',
    label: 'Events',
    labelClassName: 'text-amber-400',
    title: 'Book meetings without lifting a finger.',
    description:
      'Schedule calendar events, invite the right people, and see what’s coming up next. All by asking.',
    tags: ['CALENDAR SYNC', 'INVITE GUESTS', 'UPCOMING EVENTS'],
  },
  {
    number: '03',
    label: 'Conversations',
    labelClassName: 'text-violet-400',
    title: 'Pick up where you left off.',
    description: 'Every conversation is saved. Revisit what was said, or jump back into a call in one tap.',
    tags: ['TRANSCRIPTS', 'SESSION HISTORY', 'RESUME ANYTIME'],
  },
]

export default function LandingPage() {
  const [open, setOpen] = useState(false)
  const apiUrl = import.meta.env.VITE_API_URL ?? ''
  const googleLoginUrl = `${apiUrl}/api/v1/auth/google/login`

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b border-border border-stone-300">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 md:px-8 border-x border-stone-300">
          <span className="font-heading text-lg font-semibold">Voice Agent</span>
          <Button variant="default" onClick={() => setOpen(true)}>
            Sign in
          </Button>
        </div>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Sign in</DialogTitle>
            <DialogDescription>
              Continue with your Google account to get started.
            </DialogDescription>
          </DialogHeader>
          <Button variant="outline" className="w-full gap-2" render={<a href={googleLoginUrl} />}>
            <GoogleIcon className="size-4" />
            Continue with Google
          </Button>
        </DialogContent>
      </Dialog>

      <div className="mx-auto max-w-7xl">
        <div className="relative">
          <img
            src="/hero-bg.webp"
            alt=""
            width={2528}
            height={1328}
            className="h-auto w-full border-x border-stone-300"
          />

          <div className="absolute inset-0 flex flex-col justify-center gap-6 p-6 md:p-14">
            <div className="max-w-lg">
              <p className="font-heading text-lg font-semibold text-black/60">
                Voice Agent
              </p>
              <h2 className="mt-2 font-heading text-3xl leading-tight font-semibold md:text-4xl">
                Manage tasks, book calendar events, and pick up where you left off. All by voice.
              </h2>
              <Button variant="default" size="lg" className="mt-6 text-lg px-8" onClick={() => setOpen(true)}>
                Sign in
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="border-y border-stone-300">
        <div className="mx-auto max-w-7xl p-6 md:p-14 border-x border-stone-300">
          <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
            <h2 className="font-heading text-4xl leading-tight font-semibold md:text-5xl">
              Tasks.
              <br />
              Events.
              <br />
              Conversations.
            </h2>
            <p className="max-w-sm text-base text-muted-foreground md:text-lg">
              One assistant, three ways to stay on top of your day. All just a conversation away.
            </p>
          </div>

          <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
            {FEATURE_CARDS.map((card) => (
              <div key={card.number} className="flex flex-col justify-between gap-6 rounded-xl bg-neutral-900 p-8">
                <div>
                  <span className="text-sm text-white/40">{card.number}</span>
                  <p className={`mt-4 text-sm font-medium ${card.labelClassName}`}>{card.label}</p>
                  <h3 className="mt-2 text-2xl font-semibold leading-snug text-white">{card.title}</h3>
                  <p className="mt-4 text-sm text-white/70">{card.description}</p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {card.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium tracking-wide text-white/70"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <Button variant="secondary" className="w-fit" render={<a href={googleLoginUrl} />}>
                  Get started
                </Button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <footer className="border-stone-300 py-4 text-center text-xs text-muted-foreground border-x max-w-7xl mx-auto">
        &copy; {new Date().getFullYear()} Voice Agent. All rights reserved.
      </footer>
    </div>
  )
}
