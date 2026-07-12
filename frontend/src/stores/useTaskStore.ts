import { create } from 'zustand'
import { api } from '@/lib/api'

export interface Task {
  id: string
  title: string
  status: 'not_started' | 'in_progress' | 'completed'
  duration_minutes: number | null
  created_at: string
}

interface TaskState {
  tasks: Task[]
  loading: boolean
  error: string | null
}

interface TaskActions {
  list: () => Promise<void>
  add: (title: string, durationMinutes?: number | null) => Promise<void>
  setStatus: (id: string, status: string) => Promise<void>
  remove: (id: string) => Promise<void>
}

export const useTaskStore = create<TaskState & TaskActions>((set, get) => ({
  tasks: [],
  loading: false,
  error: null,

  list: async () => {
    set({ loading: true, error: null })
    try {
      const res = await api.get<{ data: Task[] }>('/tasks')
      set({ tasks: res.data.data, loading: false })
    } catch {
      set({ error: 'Failed to load tasks', loading: false })
    }
  },

  add: async (title: string, durationMinutes?: number | null) => {
    const res = await api.post<{ data: Task }>('/tasks', { title, duration_minutes: durationMinutes ?? null })
    set({ tasks: [...get().tasks, res.data.data] })
  },

  setStatus: async (id: string, status: string) => {
    const prev = get().tasks.find((t) => t.id === id)
    set({ tasks: get().tasks.map((t) => (t.id === id ? { ...t, status: status as Task['status'] } : t)) })
    try {
      await api.patch<{ data: Task }>(`/tasks/${id}/status`, { status })
    } catch {
      if (prev) set({ tasks: get().tasks.map((t) => (t.id === id ? prev : t)) })
    }
  },

  remove: async (id: string) => {
    set({ tasks: get().tasks.filter((t) => t.id !== id) })
    try {
      await api.delete(`/tasks/${id}`)
    } catch {
      set({ tasks: get().tasks })
    }
  },
}))
