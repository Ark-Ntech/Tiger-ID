import { Fragment, useEffect, useCallback, useRef } from 'react'
import { NavLink } from 'react-router-dom'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon, UserCircleIcon } from '@heroicons/react/24/outline'
import { cn } from '../../utils/cn'

interface NavigationItem {
  name: string
  to: string
  icon: React.ComponentType<{ className?: string }>
}

interface MobileNavProps {
  isOpen: boolean
  onClose: () => void
  navigation: NavigationItem[]
  user?: {
    name: string
    email: string
    avatar?: string
  }
}

const MobileNav = ({ isOpen, onClose, navigation, user }: MobileNavProps) => {
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  // Handle Escape key
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose()
      }
    },
    [isOpen, onClose]
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown])

  // Handle navigation click - close the drawer
  const handleNavClick = () => {
    onClose()
  }

  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog
        as="div"
        className="relative z-50 md:hidden"
        onClose={onClose}
        initialFocus={closeButtonRef}
        data-testid="mobile-nav-dialog"
      >
        {/* Backdrop with blur */}
        <Transition.Child
          as={Fragment}
          enter="transition-opacity ease-linear duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="transition-opacity ease-linear duration-300"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div
            className="fixed inset-0 bg-tactical-950/80 backdrop-blur-sm"
            data-testid="mobile-nav-backdrop"
            aria-hidden="true"
          />
        </Transition.Child>

        {/* Slide-out drawer */}
        <div className="fixed inset-0 flex">
          <Transition.Child
            as={Fragment}
            enter="transition ease-in-out duration-300 transform"
            enterFrom="-translate-x-full"
            enterTo="translate-x-0"
            leave="transition ease-in-out duration-300 transform"
            leaveFrom="translate-x-0"
            leaveTo="-translate-x-full"
          >
            <Dialog.Panel
              className={cn(
                'relative flex w-full max-w-xs flex-col',
                'bg-tactical-950 text-white',
                'h-full overflow-y-auto',
                'shadow-2xl'
              )}
              data-testid="mobile-nav-panel"
            >
              {/* Close button */}
              <div className="absolute right-0 top-0 pt-4 pr-4">
                <button
                  ref={closeButtonRef}
                  type="button"
                  className={cn(
                    'rounded-lg p-2',
                    'text-tactical-400 hover:text-white',
                    'hover:bg-tactical-800',
                    'focus:outline-none focus:ring-2 focus:ring-tiger-orange',
                    'transition-colors duration-200'
                  )}
                  onClick={onClose}
                  data-testid="mobile-nav-close-button"
                >
                  <span className="sr-only">Close sidebar</span>
                  <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                </button>
              </div>

              {/* Logo / Header */}
              <div
                className="flex items-center space-x-3 p-6 border-b border-tactical-800"
                data-testid="mobile-nav-logo"
              >
                <div className="text-3xl" aria-hidden="true">
                  <span role="img" aria-label="Tiger">🐅</span>
                </div>
                <div>
                  <Dialog.Title className="text-xl font-bold text-white">
                    Tiger ID
                  </Dialog.Title>
                  <p className="text-xs text-tactical-400">Investigation System</p>
                </div>
              </div>

              {/* Navigation Links */}
              <nav
                className="flex-1 p-4 space-y-1"
                data-testid="mobile-nav-navigation"
                aria-label="Mobile navigation"
              >
                {navigation.map((item) => (
                  <NavLink
                    key={item.name}
                    to={item.to}
                    end={item.to === '/'}
                    onClick={handleNavClick}
                    data-testid={`mobile-nav-link-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                        isActive
                          ? 'bg-tiger-orange text-white'
                          : 'text-tactical-300 hover:bg-tactical-800 hover:text-white'
                      )
                    }
                  >
                    <item.icon className="h-5 w-5" aria-hidden="true" />
                    <span className="text-sm font-medium">{item.name}</span>
                  </NavLink>
                ))}
              </nav>

              {/* User Info Footer */}
              {user && (
                <div
                  className="p-4 border-t border-tactical-800"
                  data-testid="mobile-nav-user-info"
                >
                  <div className="flex items-center space-x-3">
                    {user.avatar ? (
                      <img
                        src={user.avatar}
                        alt={`${user.name}'s avatar`}
                        className="h-10 w-10 rounded-full object-cover ring-2 ring-tactical-700"
                        data-testid="mobile-nav-user-avatar"
                      />
                    ) : (
                      <UserCircleIcon
                        className="h-10 w-10 text-tactical-400"
                        aria-hidden="true"
                        data-testid="mobile-nav-user-icon"
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <p
                        className="text-sm font-medium text-white truncate"
                        data-testid="mobile-nav-user-name"
                      >
                        {user.name}
                      </p>
                      <p
                        className="text-xs text-tactical-400 truncate"
                        data-testid="mobile-nav-user-email"
                      >
                        {user.email}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Version Footer */}
              <div className="p-4 border-t border-tactical-800">
                <div className="text-xs text-tactical-400 text-center">
                  <p data-testid="mobile-nav-version">Version 1.0.0</p>
                  <p className="mt-1">© 2024 Tiger ID</p>
                </div>
              </div>
            </Dialog.Panel>
          </Transition.Child>

          {/* Empty space on the right side (clickable to close via Dialog's onClose) */}
          <div className="w-14 flex-shrink-0" aria-hidden="true" />
        </div>
      </Dialog>
    </Transition>
  )
}

export default MobileNav
