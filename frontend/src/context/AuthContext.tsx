import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useNavigate } from 'react-router-dom'
import { getCurrentUser, loginUser, registerUser } from '../api/auth'
import { setUnauthorizedHandler } from '../api/client'
import { clearToken, getToken, setToken } from '../api/token'
import type { User, UserCreate } from '../types'
import { getErrorMessage } from '../utils/errors'

interface AuthContextValue {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  register: (payload: UserCreate) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
    navigate('/login', { replace: true })
  }, [navigate])

  const refreshUser = useCallback(async () => {
    const token = getToken()
    if (!token) {
      setUser(null)
      return
    }
    const me = await getCurrentUser()
    setUser(me)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null)
      navigate('/login', { replace: true })
    })
    return () => setUnauthorizedHandler(null)
  }, [navigate])

  useEffect(() => {
    let active = true
    async function bootstrap() {
      const token = getToken()
      if (!token) {
        if (active) {
          setLoading(false)
        }
        return
      }
      try {
        const me = await getCurrentUser()
        if (active) {
          setUser(me)
        }
      } catch {
        clearToken()
        if (active) {
          setUser(null)
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }
    void bootstrap()
    return () => {
      active = false
    }
  }, [])

  const login = useCallback(
    async (username: string, password: string) => {
      clearToken()
      try {
        const token = await loginUser(username, password)
        setToken(token.access_token)
        const me = await getCurrentUser()
        setUser(me)
        navigate('/dashboard', { replace: true })
      } catch (error) {
        clearToken()
        throw new Error(getErrorMessage(error, 'Login failed'))
      }
    },
    [navigate],
  )

  const register = useCallback(async (payload: UserCreate) => {
    try {
      await registerUser(payload)
    } catch (error) {
      throw new Error(getErrorMessage(error, 'Registration failed'))
    }
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, loading, login, register, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
