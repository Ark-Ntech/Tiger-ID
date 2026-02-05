import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '../hooks/useAuth'
import Button from '../components/common/Button'
import Input from '../components/common/Input'
import Alert from '../components/common/Alert'

const requestSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
})

const confirmSchema = z
  .object({
    new_password: z.string().min(8, 'Password must be at least 8 characters'),
    confirm_password: z.string().min(8, 'Password must be at least 8 characters'),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords don't match",
    path: ['confirm_password'],
  })

type RequestForm = z.infer<typeof requestSchema>
type ConfirmForm = z.infer<typeof confirmSchema>

const PasswordReset = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const {
    requestPasswordReset,
    confirmPasswordReset,
    isRequestingReset,
    isConfirmingReset,
  } = useAuth()

  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Request form
  const {
    register: registerRequest,
    handleSubmit: handleSubmitRequest,
    formState: { errors: requestErrors },
  } = useForm<RequestForm>({
    resolver: zodResolver(requestSchema),
  })

  // Confirm form
  const {
    register: registerConfirm,
    handleSubmit: handleSubmitConfirm,
    formState: { errors: confirmErrors },
  } = useForm<ConfirmForm>({
    resolver: zodResolver(confirmSchema),
  })

  const onRequestSubmit = async (data: RequestForm) => {
    try {
      setError(null)
      await requestPasswordReset(data.email)
      setSuccess(true)
    } catch (err: any) {
      setError(
        err?.data?.message ||
          err?.data?.detail ||
          err?.message ||
          'Failed to send password reset email'
      )
    }
  }

  const onConfirmSubmit = async (data: ConfirmForm) => {
    if (!token) {
      setError('Invalid reset token')
      return
    }

    try {
      setError(null)
      await confirmPasswordReset(token, data.new_password)
      setSuccess(true)
      setTimeout(() => navigate('/login'), 3000)
    } catch (err: any) {
      setError(
        err?.data?.message ||
          err?.data?.detail ||
          err?.message ||
          'Failed to reset password'
      )
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-500 to-primary-700 px-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-xl p-8">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">🐅</div>
            <h1 className="text-2xl font-bold text-gray-900">
              {token ? 'Reset Password' : 'Forgot Password'}
            </h1>
            <p className="text-gray-600 mt-2">
              {token
                ? 'Enter your new password'
                : 'Enter your email to reset your password'}
            </p>
          </div>

          {/* Success Alert */}
          {success && (
            <Alert type="success" className="mb-6">
              {token
                ? 'Password reset successful! Redirecting to login...'
                : 'Password reset email sent. Please check your inbox.'}
            </Alert>
          )}

          {/* Error Alert */}
          {error && (
            <Alert type="error" className="mb-6">
              {error}
            </Alert>
          )}

          {!success && !token && (
            <form
              onSubmit={handleSubmitRequest(onRequestSubmit)}
              className="space-y-6"
            >
              <Input
                label="Email Address"
                type="email"
                {...registerRequest('email')}
                error={requestErrors.email?.message}
                placeholder="Enter your email"
                autoComplete="email"
              />

              <Button
                type="submit"
                variant="primary"
                className="w-full"
                size="lg"
                isLoading={isRequestingReset}
              >
                Send Reset Link
              </Button>
            </form>
          )}

          {!success && token && (
            <form
              onSubmit={handleSubmitConfirm(onConfirmSubmit)}
              className="space-y-6"
            >
              <Input
                label="New Password"
                type="password"
                {...registerConfirm('new_password')}
                error={confirmErrors.new_password?.message}
                placeholder="Enter new password"
                autoComplete="new-password"
              />

              <Input
                label="Confirm Password"
                type="password"
                {...registerConfirm('confirm_password')}
                error={confirmErrors.confirm_password?.message}
                placeholder="Confirm new password"
                autoComplete="new-password"
              />

              <Button
                type="submit"
                variant="primary"
                className="w-full"
                size="lg"
                isLoading={isConfirmingReset}
              >
                Reset Password
              </Button>
            </form>
          )}

          {/* Back to Login */}
          <div className="mt-6 text-center">
            <a
              href="/login"
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              Back to Login
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PasswordReset
