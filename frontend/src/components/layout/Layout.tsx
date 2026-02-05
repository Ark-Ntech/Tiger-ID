import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import {
  Bars3Icon,
  HomeIcon,
  MagnifyingGlassCircleIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  CheckBadgeIcon,
  SignalIcon,
} from '@heroicons/react/24/outline'
import Sidebar from './Sidebar'
import Header from './Header'
import MobileNav from './MobileNav'
import { useAuth } from '../../hooks/useAuth'
import { cn } from '../../utils/cn'

// Tiger icon as a simple component since Heroicons doesn't have one
const TigerIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M12 2C7 2 3 6 3 11c0 3 1.5 5.5 4 7v2h10v-2c2.5-1.5 4-4 4-7 0-5-4-9-9-9z" />
    <path d="M8 11v.01M16 11v.01" />
    <path d="M9 16c.5.5 1.5 1 3 1s2.5-.5 3-1" />
  </svg>
)

// Navigation items - shared between Sidebar and MobileNav
const navigation = [
  { name: 'Home', to: '/', icon: HomeIcon },
  { name: 'Dashboard', to: '/dashboard', icon: ChartBarIcon },
  { name: 'Investigation', to: '/investigation2', icon: MagnifyingGlassCircleIcon },
  { name: 'Tigers', to: '/tigers', icon: TigerIcon },
  { name: 'Facilities', to: '/facilities', icon: BuildingOfficeIcon },
  { name: 'Verification', to: '/verification', icon: CheckBadgeIcon },
  { name: 'Discovery', to: '/discovery', icon: SignalIcon },
]

const Layout = () => {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const { user } = useAuth()

  // Format user data for MobileNav
  const mobileNavUser = user
    ? {
        name: user.full_name || user.username || 'User',
        email: user.email || '',
        avatar: undefined, // Add avatar URL if available in user object
      }
    : undefined

  return (
    <div
      className={cn(
        'flex h-screen overflow-hidden',
        'bg-tactical-50 dark:bg-tactical-950',
        'transition-colors duration-200'
      )}
    >
      {/* Mobile Navigation Drawer */}
      <MobileNav
        isOpen={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        navigation={navigation}
        user={mobileNavUser}
      />

      {/* Desktop Sidebar - hidden on mobile */}
      <div className="hidden md:flex">
        <Sidebar />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header with mobile hamburger button */}
        <div className="relative">
          {/* Mobile hamburger button */}
          <button
            type="button"
            className={cn(
              'absolute left-4 top-1/2 -translate-y-1/2 z-10',
              'md:hidden',
              'p-2 rounded-lg',
              'text-tactical-600 dark:text-tactical-400',
              'hover:bg-tactical-100 dark:hover:bg-tactical-800',
              'hover:text-tactical-900 dark:hover:text-white',
              'focus:outline-none focus:ring-2 focus:ring-tiger-orange focus:ring-offset-2',
              'focus:ring-offset-white dark:focus:ring-offset-tactical-900',
              'transition-colors duration-200'
            )}
            onClick={() => setMobileNavOpen(true)}
            data-testid="mobile-nav-hamburger-button"
            aria-label="Open navigation menu"
            aria-expanded={mobileNavOpen}
            aria-controls="mobile-nav-dialog"
          >
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>

          {/* Header with padding adjustment for hamburger on mobile */}
          <div className="md:pl-0 pl-14">
            <Header />
          </div>
        </div>

        {/* Page Content */}
        <main
          className={cn(
            'flex-1 overflow-y-auto p-6',
            'bg-tactical-50 dark:bg-tactical-950',
            'transition-colors duration-200'
          )}
        >
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
