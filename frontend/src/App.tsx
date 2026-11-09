import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router'
import { Toaster } from '@/components/ui/sonner'
import ProtectedRoute from '@/components/ProtectedRoute'
import LandingPage from '@/pages/Landing'
import NotFoundPage from '@/pages/NotFound'

// Everything behind login (incl. livekit-client) is split out of the landing bundle.
const DashboardLayout = lazy(() => import('@/components/DashboardLayout'))
const TasksPage = lazy(() => import('@/pages/Tasks'))
const EventsPage = lazy(() => import('@/pages/Events'))
const ConversationTranscriptPage = lazy(() => import('@/pages/ConversationTranscript'))
const VoiceAssistantPage = lazy(() => import('@/pages/VoiceAssistant'))
import { useAuthStore } from '@/stores/useAuthStore'

export default function App() {
  const initialize = useAuthStore((s) => s.initialize)

  useEffect(() => {
    void initialize()
  }, [initialize])

  return (
    <>
      <Toaster richColors closeButton position="top-right" />
      <Suspense>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<Navigate to="/voice" replace />} />
            <Route path="/voice" element={<VoiceAssistantPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/conversations/:conversationId" element={<ConversationTranscriptPage />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      </Suspense>
    </>
  )
}
