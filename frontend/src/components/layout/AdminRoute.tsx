import { Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export function AdminRoute() {
  const { user } = useAuth()

  if (!user?.is_admin) {
    return (
      <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
        This page requires an admin account. Ask whoever set up the database to run:
        <code className="mx-1 rounded bg-amber-100 px-1.5 py-0.5">
          UPDATE users SET is_admin = true WHERE email = '{user?.email ?? "you@example.com"}';
        </code>
      </div>
    )
  }
  return <Outlet />
}
