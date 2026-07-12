import { useEffect } from 'react'
import { Route, Routes } from 'react-router'
import { Toaster } from '@/components/ui/sonner'
import DashboardLayout from '@/components/DashboardLayout'
import ProtectedRoute from '@/components/ProtectedRoute'
import LandingPage from '@/pages/Landing'
import DashboardPage from '@/pages/Dashboard'
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
            <Route path="/dashboard" element={<DashboardPage />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </>
  )
}
