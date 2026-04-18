import { useEffect, useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { AuthContext } from '@/hooks/auth-context'
import { api } from '@/services/api'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('heritage_token'))
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('heritage_user')
    return raw ? JSON.parse(raw) : null
  })

  const loginMutation = useMutation({
    mutationFn: async ({ email, password }) => {
      const { data } = await api.post('/auth/login', { email, password })
      return data
    },
    onSuccess: (data) => {
      localStorage.setItem('heritage_token', data.access_token)
      setToken(data.access_token)
      if (data.user) {
        localStorage.setItem('heritage_user', JSON.stringify(data.user))
        setUser(data.user)
      }
    },
  })

  const registerMutation = useMutation({
    mutationFn: async ({ email, password, full_name }) => {
      const { data } = await api.post('/auth/register', { email, password, full_name })
      return data
    },
    onSuccess: (data) => {
      localStorage.setItem('heritage_user', JSON.stringify(data))
      setUser(data)
    },
  })

  const logout = () => {
    localStorage.removeItem('heritage_token')
    localStorage.removeItem('heritage_user')
    setToken(null)
    setUser(null)
  }

  useEffect(() => {
    if (!token || user) return

    let cancelled = false
    const loadCurrentUser = async () => {
      try {
        const { data } = await api.get('/auth/me')
        if (cancelled) return
        localStorage.setItem('heritage_user', JSON.stringify(data))
        setUser(data)
      } catch {
        if (cancelled) return
        localStorage.removeItem('heritage_token')
        localStorage.removeItem('heritage_user')
        setToken(null)
        setUser(null)
      }
    }

    loadCurrentUser()
    return () => {
      cancelled = true
    }
  }, [token, user])

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      loginMutation,
      registerMutation,
      logout,
      setUser,
    }),
    [token, user, loginMutation, registerMutation],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
