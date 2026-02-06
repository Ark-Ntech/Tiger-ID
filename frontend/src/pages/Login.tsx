import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '../hooks/useAuth'
import Button from '../components/common/Button'
import Input from '../components/common/Input'
import Alert from '../components/common/Alert'

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
  remember_me: z.boolean().optional(),
})

type LoginForm = z.infer<typeof loginSchema>

const Login = () => {
  const navigate = useNavigate()
  const { login, isAuthenticated, error: authError } = useAuth()
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      remember_me: false,
    },
  })

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/')
    }
  }, [isAuthenticated, navigate])

  useEffect(() => {
    if (authError) {
      setError(authError)
    }
  }, [authError])

  const onSubmit = async (data: LoginForm) => {
    try {
      setError(null)
      await login(data)
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.')
    }
  }

  return (
    <div className="min-h-screen h-full flex items-center justify-center bg-gradient-to-br from-tiger-orange to-tiger-orange-dark px-4 py-8">
      <div className="max-w-md w-full mx-auto">
        <div className="bg-white rounded-lg shadow-xl p-8">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">🐅</div>
            <h1 className="text-3xl font-bold text-gray-900">Tiger ID</h1>
            <p className="text-gray-600 mt-2">Investigation System</p>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert type="error" className="mb-6">
              {error}
            </Alert>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <Input
              label="Username"
              {...register('username')}
              error={errors.username?.message}
              placeholder="Enter your username"
              autoComplete="username"
            />

            <Input
              label="Password"
              type="password"
              {...register('password')}
              error={errors.password?.message}
              placeholder="Enter your password"
              autoComplete="current-password"
            />

            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  {...register('remember_me')}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-600">Remember me</span>
              </label>

              <a
                href="/password-reset"
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Forgot password?
              </a>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              size="lg"
              isLoading={isSubmitting}
            >
              Sign In
            </Button>
          </form>

          {/* Footer */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Need access?{' '}
              <a href="#" className="text-primary-600 hover:text-primary-700">
                Contact Administrator
              </a>
            </p>
          </div>
        </div>

        {/* Version */}
        <div className="mt-8 text-center text-white text-sm">
          <p>Version 2.0.0</p>
        </div>
      </div>
    </div>
  )
}

export default Login

