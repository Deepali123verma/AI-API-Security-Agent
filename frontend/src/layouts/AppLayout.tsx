import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  Bell,
  ChevronDown,
  GitCompareArrows,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  Route,
  ScanSearch,
  Search,
  Shield,
  ShieldAlert,
  X,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const navItems = [
  {
    to: '/dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    isActive: (pathname: string, _search?: string) => pathname === '/dashboard',
  },
  {
    to: '/scans',
    label: 'Scans',
    icon: ScanSearch,
    isActive: (pathname: string, search = '') =>
      pathname === '/scans' && !new URLSearchParams(search).get('tab'),
  },
  {
    to: '/endpoints',
    label: 'Endpoints',
    icon: Route,
    isActive: (pathname: string, _search?: string) =>
      pathname.startsWith('/endpoints') || /\/scans\/\d+\/endpoints/.test(pathname),
  },
  {
    to: '/findings',
    label: 'Findings',
    icon: ShieldAlert,
    isActive: (pathname: string, _search?: string) =>
      pathname.startsWith('/findings') || /\/scans\/\d+\/findings/.test(pathname),
  },
  {
    to: '/regression',
    label: 'Regression / Compare',
    icon: GitCompareArrows,
    isActive: (pathname: string, _search?: string) =>
      pathname.startsWith('/regression') || pathname.includes('/compare'),
  },
  {
    to: '/scans?tab=history',
    label: 'Scan History',
    icon: History,
    isActive: (pathname: string, search: string) =>
      pathname === '/scans' && new URLSearchParams(search).get('tab') === 'history',
  },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [search, setSearch] = useState('')
  const menuRef = useRef<HTMLDivElement>(null)

  const initials = useMemo(() => {
    const name = user?.username || 'U'
    return name.slice(0, 2).toUpperCase()
  }, [user])

  useEffect(() => {
    function onDocClick(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', onDocClick)
    return () => document.removeEventListener('mousedown', onDocClick)
  }, [])

  function submitSearch(event: FormEvent) {
    event.preventDefault()
    const q = search.trim()
    navigate(q ? `/scans?q=${encodeURIComponent(q)}` : '/scans')
    setMobileOpen(false)
  }

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        document.getElementById('global-search')?.focus()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  return (
    <div className="min-h-screen bg-[#eef2f7] text-slate-900">
      <div className="flex min-h-screen">
        <aside
          className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-slate-800/80 bg-[var(--navy-950)] text-slate-100 transition-transform duration-200 lg:static lg:translate-x-0 ${
            mobileOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <div className="flex h-[4.5rem] items-center gap-3 border-b border-slate-800 px-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-500/15 ring-1 ring-sky-400/30">
              <Shield className="h-5 w-5 text-sky-400" aria-hidden />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-tight">AI API Security Agent</p>
              <p className="text-[11px] text-slate-400">Deterministic + Gemini reasoning</p>
            </div>
          </div>

          <nav className="flex-1 space-y-1 p-3" aria-label="Main">
            {navItems.map((item) => {
              const active = item.isActive(location.pathname, location.search)
              return (
                <NavLink
                  key={item.to + item.label}
                  to={item.to}
                  onClick={() => setMobileOpen(false)}
                  className={() =>
                    `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all ${
                      active
                        ? 'nav-active-glow bg-sky-500/15 text-sky-100'
                        : 'text-slate-300 hover:bg-white/5 hover:text-white'
                    }`
                  }
                >
                  <item.icon className="h-4 w-4 shrink-0" aria-hidden />
                  {item.label}
                </NavLink>
              )
            })}
          </nav>

          <div className="p-4">
            <div className="sidebar-status rounded-2xl p-4">
              <p className="text-sm font-semibold text-sky-100">Secure APIs.</p>
              <p className="text-sm font-semibold text-white">Safer Tomorrow.</p>
              <p className="mt-3 text-[11px] uppercase tracking-[0.16em] text-slate-400">
                Detect · Analyze · Protect
              </p>
            </div>
          </div>
        </aside>

        {mobileOpen ? (
          <button
            type="button"
            className="fixed inset-0 z-30 bg-slate-950/50 lg:hidden"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
          />
        ) : null}

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/90 backdrop-blur-md">
            <div className="flex h-[4.5rem] items-center gap-3 px-4 sm:px-6">
              <button
                type="button"
                className="rounded-xl border border-slate-300 p-2 text-slate-700 lg:hidden focus-ring"
                onClick={() => setMobileOpen((open) => !open)}
                aria-label="Toggle navigation"
              >
                {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
              </button>

              <form onSubmit={submitSearch} className="hidden min-w-0 flex-1 md:block">
                <label htmlFor="global-search" className="sr-only">
                  Search
                </label>
                <div className="relative max-w-xl">
                  <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    id="global-search"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search scans, endpoints, findings..."
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-16 text-sm outline-none ring-sky-500 transition focus:bg-white focus:ring-2"
                  />
                  <span className="pointer-events-none absolute right-3 top-2.5 rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-400">
                    ⌘K
                  </span>
                </div>
              </form>

              <div className="ml-auto flex items-center gap-2 sm:gap-3">
                <button
                  type="button"
                  className="relative rounded-xl border border-slate-200 bg-white p-2 text-slate-600 hover:bg-slate-50 focus-ring"
                  aria-label="Notifications"
                  title="No new notifications"
                >
                  <Bell className="h-4 w-4" />
                  <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-sky-500 pulse-dot" />
                </button>

                <div className="relative" ref={menuRef}>
                  <button
                    type="button"
                    onClick={() => setMenuOpen((open) => !open)}
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 hover:bg-slate-50 focus-ring"
                    aria-expanded={menuOpen}
                    aria-haspopup="menu"
                  >
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                      {initials}
                    </span>
                    <span className="hidden text-left sm:block">
                      <span className="block text-sm font-medium text-slate-900">{user?.username}</span>
                      <span className="block max-w-[10rem] truncate text-xs text-slate-500">
                        {user?.email}
                      </span>
                    </span>
                    <ChevronDown className="hidden h-4 w-4 text-slate-400 sm:block" />
                  </button>

                  {menuOpen ? (
                    <div
                      role="menu"
                      className="absolute right-0 mt-2 w-56 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-xl animate-fade-up"
                    >
                      <div className="border-b border-slate-100 px-3 py-2">
                        <p className="text-sm font-medium text-slate-900">{user?.username}</p>
                        <p className="truncate text-xs text-slate-500">{user?.email}</p>
                      </div>
                      <Link
                        to="/dashboard"
                        role="menuitem"
                        className="block px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                        onClick={() => setMenuOpen(false)}
                      >
                        Dashboard
                      </Link>
                      <Link
                        to="/scans"
                        role="menuitem"
                        className="block px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                        onClick={() => setMenuOpen(false)}
                      >
                        Scan history
                      </Link>
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                          setMenuOpen(false)
                          logout()
                        }}
                        className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-rose-700 hover:bg-rose-50"
                      >
                        <LogOut className="h-4 w-4" />
                        Sign out
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </header>

          <main className="flex-1 p-4 sm:p-6 lg:p-8">
            <div className="mx-auto max-w-7xl">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
