import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

let resetAuthStore: (() => void) | null = null

export function registerAuthReset(fn: () => void) {
  resetAuthStore = fn
}

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value: unknown) => void
  reject: (reason: unknown) => void
}> = []

function processQueue(error: unknown) {
  for (const prom of failedQueue) {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(undefined)
    }
  }
  failedQueue = []
}

// access_token is short-lived; when a request 401s, try refresh_token once
// (via the cookie-scoped /auth/refresh endpoint) and retry the original
// request. Concurrent requests that 401 while a refresh is already in
// flight queue up instead of each triggering their own refresh call.
api.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || error.response?.status !== 401) {
      return Promise.reject(error)
    }

    const originalRequest = error.config as (typeof error.config & { _retry?: boolean }) | undefined
    if (!originalRequest || originalRequest._retry || originalRequest.url?.includes('/auth/refresh')) {
      resetAuthStore?.()
      if (window.location.pathname !== '/') window.location.href = '/'
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then(() => api(originalRequest))
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      await api.post('/auth/refresh')
      processQueue(null)
      return api(originalRequest)
    } catch (refreshError) {
      processQueue(refreshError)
      resetAuthStore?.()
      if (window.location.pathname !== '/') window.location.href = '/'
      return Promise.reject(error)
    } finally {
      isRefreshing = false
    }
  },
)
