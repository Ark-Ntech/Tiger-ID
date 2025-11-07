import { Link } from 'react-router-dom'
import Button from '../components/common/Button'
import { HomeIcon } from '@heroicons/react/24/outline'

const NotFound = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-gray-300">404</h1>
        <h2 className="text-3xl font-bold text-gray-900 mt-4">Page Not Found</h2>
        <p className="text-gray-600 mt-2 mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link to="/">
          <Button variant="primary" className="inline-flex items-center gap-2">
            <HomeIcon className="h-5 w-5" />
            Go Home
          </Button>
        </Link>
      </div>
    </div>
  )
}

export default NotFound

