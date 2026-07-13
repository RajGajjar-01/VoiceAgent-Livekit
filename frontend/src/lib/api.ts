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

function errorTitle(error: unknown): string | undefined {
  if (!axios.isAxiosError(error)) return undefined
  const data = error.response?.data as { error?: { title?: string } } | undefined
  return data?.error?.title
}

function forceLogout(reason: string, error: unknown) {
  console.warn(`[auth] logging out: ${reason}`, { title: errorTitle(error) })
  resetAuthStore?.()
  if (window.location.pathname !== '/') window.location.href = '/'
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
    if (!originalRequest) {
      forceLogout('401 with no request config to retry', error)
      return Promise.reject(error)
    }
    if (originalRequest.url?.includes('/auth/refresh')) {
      // The refresh call itself came back 401 — the refresh_token cookie is
      // missing, expired, or invalid (see the backend's refresh_failed log
      // for which). No further retry is possible.
      forceLogout(`refresh call itself 401'd (${originalRequest.url})`, error)
      return Promise.reject(error)
    }
    if (originalRequest._retry) {
      // We already refreshed once for this request and it 401'd again
      // immediately after — the new access_token isn't being honored, so
      // retrying further would just loop.
      forceLogout(`retry after refresh still 401'd (${originalRequest.url})`, error)
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then(() => api(originalRequest))
    }

    originalRequest._retry = true
    isRefreshing = true

    console.info(`[auth] access token expired, refreshing (triggered by ${originalRequest.url})`)
    try {
      await api.post('/auth/refresh')
      console.info('[auth] refresh succeeded, retrying original request')
      processQueue(null)
      return api(originalRequest)
    } catch (refreshError) {
      forceLogout('refresh request failed', refreshError)
      processQueue(refreshError)
      return Promise.reject(error)
    } finally {
      isRefreshing = false
    }
  },
)
