import { useState, useEffect } from 'react'
import {
  BellIcon,
  MagnifyingGlassIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  SunIcon,
  MoonIcon,
} from '@heroicons/react/24/outline'
import { Menu, Transition } from '@headlessui/react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useAppSelector } from '../../app/hooks'
import { cn } from '../../utils/cn'

// Dark mode hook
const useDarkMode = () => {
  const [isDark, setIsDark] = useState(() => {
    // Check localStorage first
    const stored = localStorage.getItem('tiger-id-theme')
    if (stored) {
      return stored === 'dark'
    }
    // Then check system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    const root = document.documentElement

    if (isDark) {
      root.classList.add('dark')
      localStorage.setItem('tiger-id-theme', 'dark')
    } else {
      root.classList.remove('dark')
      localStorage.setItem('tiger-id-theme', 'light')
    }
  }, [isDark])

  // Listen for system preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const handleChange = (e: MediaQueryListEvent) => {
      const stored = localStorage.getItem('tiger-id-theme')
      // Only auto-switch if user hasn't set a preference
      if (!stored) {
        setIsDark(e.matches)
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  return [isDark, setIsDark] as const
}

const Header = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const notifications = useAppSelector((state) => state.notifications.notifications)
  const unreadCount = useAppSelector((state) => state.notifications.unreadCount)
  const [searchQuery, setSearchQuery] = useState('')
  const [isDark, setIsDark] = useDarkMode()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim() && searchQuery.trim().length >= 2) {
      // Navigate to search results page with query
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  const toggleDarkMode = () => {
    setIsDark(!isDark)
  }

  return (
    <header className={cn(
      'bg-white dark:bg-tactical-900 shadow-sm',
      'border-b border-tactical-200 dark:border-tactical-700',
      'transition-colors duration-200'
    )}>
      <div className="flex items-center justify-between px-6 py-4">
        {/* Search Bar */}
        <div className="flex-1 max-w-2xl">
          <form onSubmit={handleSearch} className="relative">
            <div className="relative">
              <MagnifyingGlassIcon className={cn(
                'absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5',
                'text-tactical-400 dark:text-tactical-500'
              )} />
              <input
                type="text"
                placeholder="Search investigations, tigers, facilities..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={cn(
                  'w-full pl-10 pr-4 py-2 rounded-lg',
                  'bg-tactical-50 dark:bg-tactical-800',
                  'text-tactical-900 dark:text-tactical-100',
                  'placeholder-tactical-400 dark:placeholder-tactical-500',
                  'border border-tactical-200 dark:border-tactical-700',
                  'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30 focus:border-tiger-orange',
                  'transition-all duration-200'
                )}
              />
            </div>
          </form>
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center space-x-3 ml-6">
          {/* Dark Mode Toggle */}
          <button
            onClick={toggleDarkMode}
            className={cn(
              'p-2 rounded-lg transition-colors',
              'text-tactical-500 dark:text-tactical-400',
              'hover:bg-tactical-100 dark:hover:bg-tactical-800',
              'hover:text-tactical-700 dark:hover:text-tactical-200'
            )}
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? (
              <SunIcon className="h-5 w-5" />
            ) : (
              <MoonIcon className="h-5 w-5" />
            )}
          </button>

          {/* Notifications */}
          <Menu as="div" className="relative">
            <Menu.Button className={cn(
              'relative p-2 rounded-lg transition-colors',
              'text-tactical-500 dark:text-tactical-400',
              'hover:bg-tactical-100 dark:hover:bg-tactical-800',
              'hover:text-tactical-700 dark:hover:text-tactical-200'
            )}>
              <BellIcon className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className={cn(
                  'absolute top-1 right-1 h-4 w-4 rounded-full',
                  'bg-tiger-orange text-white',
                  'text-xs font-bold flex items-center justify-center',
                  'animate-pulse-slow'
                )}>
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Menu.Button>
            <Transition
              enter="transition duration-100 ease-out"
              enterFrom="transform scale-95 opacity-0"
              enterTo="transform scale-100 opacity-100"
              leave="transition duration-75 ease-out"
              leaveFrom="transform scale-100 opacity-100"
              leaveTo="transform scale-95 opacity-0"
            >
              <Menu.Items className={cn(
                'absolute right-0 mt-2 w-80 rounded-xl shadow-tactical-lg',
                'bg-white dark:bg-tactical-800',
                'border border-tactical-200 dark:border-tactical-700',
                'ring-1 ring-black/5 focus:outline-none z-50',
                'overflow-hidden'
              )}>
                <div className="p-4">
                  <h3 className="text-sm font-semibold text-tactical-900 dark:text-tactical-100 mb-3">
                    Notifications
                  </h3>
                  {notifications.length > 0 ? (
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {notifications.slice(0, 5).map((notification) => (
                        <div
                          key={notification.id}
                          className={cn(
                            'p-3 rounded-lg transition-colors',
                            notification.read
                              ? 'bg-tactical-50 dark:bg-tactical-900/50'
                              : 'bg-tiger-orange/10 dark:bg-tiger-orange/20'
                          )}
                        >
                          <p className="text-sm font-medium text-tactical-900 dark:text-tactical-100">
                            {notification.title}
                          </p>
                          <p className="text-xs text-tactical-600 dark:text-tactical-400 mt-1">
                            {notification.message}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-tactical-500 dark:text-tactical-400 text-center py-4">
                      No notifications
                    </p>
                  )}
                </div>
              </Menu.Items>
            </Transition>
          </Menu>

          {/* User Menu */}
          <Menu as="div" className="relative">
            <Menu.Button className={cn(
              'flex items-center space-x-3 p-2 rounded-lg transition-colors',
              'hover:bg-tactical-100 dark:hover:bg-tactical-800'
            )}>
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-tactical-900 dark:text-tactical-100">
                  {user?.full_name || user?.username}
                </p>
                <p className="text-xs text-tactical-500 dark:text-tactical-400 capitalize">
                  {user?.role}
                </p>
              </div>
              <UserCircleIcon className="h-8 w-8 text-tactical-400 dark:text-tactical-500" />
            </Menu.Button>
            <Transition
              enter="transition duration-100 ease-out"
              enterFrom="transform scale-95 opacity-0"
              enterTo="transform scale-100 opacity-100"
              leave="transition duration-75 ease-out"
              leaveFrom="transform scale-100 opacity-100"
              leaveTo="transform scale-95 opacity-0"
            >
              <Menu.Items className={cn(
                'absolute right-0 mt-2 w-48 rounded-xl shadow-tactical-lg',
                'bg-white dark:bg-tactical-800',
                'border border-tactical-200 dark:border-tactical-700',
                'ring-1 ring-black/5 focus:outline-none z-50',
                'overflow-hidden'
              )}>
                <div className="p-1">
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        className={cn(
                          'flex items-center w-full px-4 py-2.5 rounded-lg text-sm',
                          'text-tactical-700 dark:text-tactical-300',
                          active && 'bg-tactical-100 dark:bg-tactical-700'
                        )}
                      >
                        <Cog6ToothIcon className="h-5 w-5 mr-3 text-tactical-500 dark:text-tactical-400" />
                        Settings
                      </button>
                    )}
                  </Menu.Item>
                  <div className="my-1 border-t border-tactical-200 dark:border-tactical-700" />
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={handleLogout}
                        className={cn(
                          'flex items-center w-full px-4 py-2.5 rounded-lg text-sm',
                          'text-red-600 dark:text-red-400',
                          active && 'bg-red-50 dark:bg-red-900/30'
                        )}
                      >
                        <ArrowRightOnRectangleIcon className="h-5 w-5 mr-3" />
                        Logout
                      </button>
                    )}
                  </Menu.Item>
                </div>
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
    </header>
  )
}

export default Header
