import { api } from './client'
import type { TokenResponse, User, UserCreate } from '../types'

export async function registerUser(payload: UserCreate): Promise<User> {
  const { data } = await api.post<User>('/auth/register', payload)
  return data
}

export async function loginUser(username: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams()
  body.set('username', username)
  body.set('password', password)

  const { data } = await api.post<TokenResponse>('/auth/login', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}
