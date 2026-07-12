import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router'
import { Toaster } from '@/components/ui/sonner'
import DashboardLayout from '@/components/DashboardLayout'
import ProtectedRoute from '@/components/ProtectedRoute'
import LandingPage from '@/pages/Landing'
import TasksPage from '@/pages/Tasks'
import EventsPage from '@/pages/Events'
import ConversationTranscriptPage from '@/pages/ConversationTranscript'
import VoiceAssistantPage from '@/pages/VoiceAssistant'
import NotFoundPage from '@/pages/NotFound'
import { useAuthStore } from '@/stores/useAuthStore'

export default function App() {
  const initialize = useAuthStore((s) => s.initialize)

  useEffect(() => {
    void initialize()
  }, [initialize])

  return (
    <>
      <Toaster richColors closeButton position="top-right" />
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
    </>
  )
}
