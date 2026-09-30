import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Money } from '../common/Money'

const NAV_LINK_CLASS = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
    isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
  }`

export function AppShell() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-1">
            <span className="mr-3 text-lg font-semibold text-slate-900">StarMarket</span>
            <NavLink to="/" end className={NAV_LINK_CLASS}>
              Dashboard
            </NavLink>
            <NavLink to="/assets" className={NAV_LINK_CLASS}>
              Assets
            </NavLink>
            <NavLink to="/portfolio" className={NAV_LINK_CLASS}>
              Portfolio
            </NavLink>
            <NavLink to="/strategies" className={NAV_LINK_CLASS}>
              Strategies
            </NavLink>
            {user?.is_admin && (
              <NavLink to="/admin" className={NAV_LINK_CLASS}>
                Admin
              </NavLink>
            )}
          </div>
          <div className="flex items-center gap-3">
            {user && (
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700">
                <Money value={user.cash_balance} />
              </span>
            )}
            <span className="text-sm text-slate-500">{user?.email}</span>
            <button
              onClick={logout}
              className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
