import { apiRequest } from './client'
import type { User } from '../types/user'

export function getMe(): Promise<User> {
  return apiRequest<User>('/me')
}
