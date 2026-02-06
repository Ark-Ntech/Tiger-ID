import { NavLink } from 'react-router-dom'
import {
  HomeIcon,
  MagnifyingGlassCircleIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  CheckBadgeIcon,
  SignalIcon,
  AdjustmentsHorizontalIcon,
  CpuChipIcon,
  CircleStackIcon,
} from '@heroicons/react/24/outline'
import { cn } from '../../utils/cn'

// Tiger icon as a simple component since Heroicons doesn't have one
const TigerIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2C7 2 3 6 3 11c0 3 1.5 5.5 4 7v2h10v-2c2.5-1.5 4-4 4-7 0-5-4-9-9-9z" />
    <path d="M8 11v.01M16 11v.01" />
    <path d="M9 16c.5.5 1.5 1 3 1s2.5-.5 3-1" />
  </svg>
)

const navigation = [
  { name: 'Home', to: '/', icon: HomeIcon },
  { name: 'Dashboard', to: '/dashboard', icon: ChartBarIcon },
  { name: 'Investigation', to: '/investigation2', icon: MagnifyingGlassCircleIcon },
  { name: 'Tigers', to: '/tigers', icon: TigerIcon },
  { name: 'Facilities', to: '/facilities', icon: BuildingOfficeIcon },
  { name: 'Verification', to: '/verification', icon: CheckBadgeIcon },
  { name: 'Discovery', to: '/discovery', icon: SignalIcon },
]

const mlNavigation = [
  { name: 'Model Weights', to: '/model-weights', icon: AdjustmentsHorizontalIcon },
  { name: 'Fine-Tuning', to: '/finetuning', icon: CpuChipIcon },
  { name: 'Datasets', to: '/dataset-management', icon: CircleStackIcon },
]

const Sidebar = () => {
  return (
    <aside
      className="w-64 bg-tactical-950 text-white min-h-screen flex flex-col"
      data-testid="sidebar"
    >
      {/* Logo */}
      <div
        className="p-6 border-b border-tactical-800"
        data-testid="sidebar-logo"
      >
        <div className="flex items-center space-x-3">
          <div className="text-3xl">🐅</div>
          <div>
            <h1 className="text-xl font-bold">Tiger ID</h1>
            <p className="text-xs text-tactical-400">Investigation System</p>
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
            data-testid={`sidebar-nav-${item.name.toLowerCase()}`}
            className={({ isActive }) =>
              cn(
                'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                isActive
                  ? 'bg-tiger-orange text-white'
                  : 'text-tactical-300 hover:bg-tactical-800 hover:text-white'
              )
            }
          >
            <item.icon className="h-5 w-5" />
            <span className="text-sm font-medium">{item.name}</span>
          </NavLink>
        ))}

        {/* ML & Data Section */}
        <div className="pt-4 mt-4 border-t border-tactical-800">
          <p className="px-4 pb-2 text-xs font-semibold text-tactical-500 uppercase tracking-wider">ML & Data</p>
          {mlNavigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.to}
              data-testid={`sidebar-nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
              className={({ isActive }) =>
                cn(
                  'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                  isActive
                    ? 'bg-tiger-orange text-white'
                    : 'text-tactical-300 hover:bg-tactical-800 hover:text-white'
                )
              }
            >
              <item.icon className="h-5 w-5" />
              <span className="text-sm font-medium">{item.name}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-tactical-800">
        <div className="text-xs text-tactical-400 text-center">
          <p data-testid="sidebar-version">Version 2.0.0</p>
          <p className="mt-1">© 2026 Tiger ID</p>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar

