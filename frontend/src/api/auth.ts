import { apiRequest } from './client'
import type { Token } from '../types/auth'

export function register(email: string, password: string, username?: string): Promise<Token> {
  return apiRequest<Token>('/auth/register', { method: 'POST', body: { email, password, username } })
}

export function login(email: string, password: string): Promise<Token> {
  return apiRequest<Token>('/auth/login', { method: 'POST', body: { email, password } })
}
