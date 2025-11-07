import { NavLink } from 'react-router-dom'
import {
  HomeIcon,
  MagnifyingGlassCircleIcon,
  FolderIcon,
  ShieldCheckIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'
import { cn } from '../../utils/cn'

const navigation = [
  { name: 'Home', to: '/', icon: HomeIcon },
  { name: 'Dashboard', to: '/dashboard', icon: ChartBarIcon },
  { name: 'Investigations', to: '/investigations', icon: FolderIcon },
  { name: 'Launch Investigation', to: '/investigations/launch', icon: MagnifyingGlassCircleIcon },
  { name: 'Tigers', to: '/tigers', icon: ShieldCheckIcon },
  { name: 'Facilities', to: '/facilities', icon: BuildingOfficeIcon },
  { name: 'Verification', to: '/verification', icon: ShieldCheckIcon },
]

const Sidebar = () => {
  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center space-x-3">
          <div className="text-3xl">🐅</div>
          <div>
            <h1 className="text-xl font-bold">Tiger ID</h1>
            <p className="text-xs text-gray-400">Investigation System</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              )
            }
          >
            <item.icon className="h-5 w-5" />
            <span className="text-sm font-medium">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-400 text-center">
          <p>Version 1.0.0</p>
          <p className="mt-1">© 2024 Tiger ID</p>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar

