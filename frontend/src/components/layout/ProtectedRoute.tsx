import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { LoadingSpinner } from '../common/LoadingSpinner'

export function ProtectedRoute() {
  const { status } = useAuth()

  if (status === 'loading') return <LoadingSpinner label="Checking session…" />
  if (status === 'unauthenticated') return <Navigate to="/login" replace />
  return <Outlet />
}
