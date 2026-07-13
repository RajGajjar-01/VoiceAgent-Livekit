import { create } from 'zustand'
import { api, registerAuthReset } from '@/lib/api'

export interface AuthUser {
  id: string
  email: string
  name: string | null
  avatar_url: string | null
}

interface AuthState {
  user: AuthUser | null
  loading: boolean
}

interface AuthActions {
  initialize: () => Promise<void>
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState & AuthActions>((set) => {
  const reset = () => set({ user: null, loading: false })

  registerAuthReset(reset)

  return {
    user: null,
    loading: true,

    initialize: async () => {
      set({ loading: true })
      try {
        const res = await api.get<{ data: AuthUser }>('/auth/me')
        set({ user: res.data.data, loading: false })
      } catch (err) {
        console.warn('[auth] initialize failed, treating as logged out', err)
        set({ user: null, loading: false })
      }
    },

    logout: async () => {
      try {
        await api.post('/auth/logout')
      } finally {
        reset()
      }
    },
  }
})
