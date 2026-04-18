import axios from 'axios'

// When VITE_API_URL is empty, use '' (relative) — requests go through Vite proxy → 127.0.0.1:8000
// When filled explicitly (e.g. production), use that value directly.
const API_BASE = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Always resolves immediately in proxy mode
export async function initApiBaseUrl() {
  return API_BASE
}

export function toApiErrorMessage(error) {
  const detail = error?.response?.data?.detail

  if (error?.response?.status === 422) {
    // Pydantic validation errors come as array of detail errors
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg || String(d)).join('; ')
    }
    return String(detail || 'Validation error. Check all fields.')
  }
  if (error?.response?.status === 409) {
    if (typeof detail === 'string' && detail.toLowerCase().includes('email already registered')) {
      return 'Email is already registered. Please log in.'
    }
    return String(detail || 'Conflict. Please try again.')
  }
  if (error?.response?.status === 401) {
    if (typeof detail === 'string' && detail.toLowerCase().includes('invalid email or password')) {
      return 'Invalid email or password.'
    }
    return String(detail || 'Authorization required.')
  }
  if (error?.response?.status === 404) {
    return typeof detail === 'string' ? detail : 'Backend endpoint not found. Please restart API.'
  }
  if (error?.response?.status === 500) {
    return 'Server internal error. Check backend logs.'
  }
  if (detail) {
    return String(detail)
  }
  if (error?.message?.includes('Network Error') || error?.code === 'ERR_NETWORK') {
    return 'Cannot connect to backend. Start FastAPI on port 8000.'
  }
  return 'Unexpected error. Please try again.'
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('heritage_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
