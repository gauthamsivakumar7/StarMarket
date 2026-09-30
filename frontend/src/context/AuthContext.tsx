import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import * as authApi from '../api/auth'
import { getMe } from '../api/me'
import { clearToken, getToken, setToken } from '../api/client'
import type { User } from '../types/user'

type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

interface AuthContextValue {
  user: User | null
  status: AuthStatus
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, username?: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  async function refreshUser() {
    const me = await getMe()
    setUser(me)
    setStatus('authenticated')
  }

  useEffect(() => {
    if (!getToken()) {
      setStatus('unauthenticated')
      return
    }
    refreshUser().catch(() => {
      clearToken()
      setStatus('unauthenticated')
    })
  }, [])

  async function login(email: string, password: string) {
    const token = await authApi.login(email, password)
    setToken(token.access_token)
    await refreshUser()
  }

  async function register(email: string, password: string, username?: string) {
    const token = await authApi.register(email, password, username)
    setToken(token.access_token)
    await refreshUser()
  }

  function logout() {
    clearToken()
    setUser(null)
    setStatus('unauthenticated')
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ user, status, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
