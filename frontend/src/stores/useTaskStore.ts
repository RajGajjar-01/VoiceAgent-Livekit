import { create } from 'zustand'
import { api } from '@/lib/api'

export interface Task {
  id: string
  title: string
  done: boolean
  created_at: string
}

interface TaskState {
  tasks: Task[]
  loading: boolean
  error: string | null
}

interface TaskActions {
  list: () => Promise<void>
  add: (title: string) => Promise<void>
  toggleDone: (id: string) => Promise<void>
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

  add: async (title: string) => {
    const res = await api.post<{ data: Task }>('/tasks', { title })
    set({ tasks: [...get().tasks, res.data.data] })
  },

  toggleDone: async (id: string) => {
    const task = get().tasks.find((t) => t.id === id)
    if (!task || task.done) return
    set({ tasks: get().tasks.map((t) => (t.id === id ? { ...t, done: true } : t)) })
    try {
      await api.patch<{ data: Task }>(`/tasks/${id}/done`)
    } catch {
      set({ tasks: get().tasks.map((t) => (t.id === id ? { ...t, done: false } : t)) })
    }
  },
}))
