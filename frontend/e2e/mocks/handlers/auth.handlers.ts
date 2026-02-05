import { http, HttpResponse, delay } from 'msw'
import { testCredentials, userFactory, type UserData } from '../../data/factories'

const API_BASE = '/api'

// Store for mock session state
let currentUser: UserData | null = null
let accessToken: string | null = null

// Helper to generate mock tokens
const generateToken = (userId: string): string => {
  return `mock_token_${userId}_${Date.now()}`
}

export const authHandlers = [
  // Login
  http.post(`${API_BASE}/auth/login`, async ({ request }) => {
    await delay(100) // Simulate network latency

    const body = await request.json() as { username: string; password: string }
    const { username, password } = body

    // Check test credentials
    const validCredentials = Object.values(testCredentials).find(
      (cred) => cred.username === username && cred.password === password
    )

    if (!validCredentials) {
      return HttpResponse.json(
        { detail: 'Invalid username or password' },
        { status: 401 }
      )
    }

    // Create user based on role
    const role = username as 'admin' | 'analyst' | 'viewer'
    currentUser = userFactory.build({ username, role })
    accessToken = generateToken(currentUser.id)

    return HttpResponse.json({
      success: true,
      access_token: accessToken,
      token_type: 'bearer',
      user: currentUser,
    })
  }),

  // Logout
  http.post(`${API_BASE}/auth/logout`, async () => {
    await delay(50)
    currentUser = null
    accessToken = null

    return HttpResponse.json({ success: true })
  }),

  // Get current user
  http.get(`${API_BASE}/auth/me`, async ({ request }) => {
    await delay(50)

    const authHeader = request.headers.get('Authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ') || !currentUser) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: currentUser,
    })
  }),

  // Refresh token
  http.post(`${API_BASE}/auth/refresh`, async ({ request }) => {
    await delay(50)

    const authHeader = request.headers.get('Authorization')
    if (!authHeader || !currentUser) {
      return HttpResponse.json(
        { detail: 'Invalid refresh token' },
        { status: 401 }
      )
    }

    accessToken = generateToken(currentUser.id)

    return HttpResponse.json({
      success: true,
      access_token: accessToken,
      token_type: 'bearer',
    })
  }),

  // Password reset request
  http.post(`${API_BASE}/auth/password-reset/request`, async ({ request }) => {
    await delay(100)

    const body = await request.json() as { email: string }
    const { email } = body

    // Always return success (don't reveal if email exists)
    return HttpResponse.json({
      success: true,
      message: 'If an account with that email exists, a password reset link has been sent.',
    })
  }),

  // Password reset confirm
  http.post(`${API_BASE}/auth/password-reset/confirm`, async ({ request }) => {
    await delay(100)

    const body = await request.json() as { token: string; new_password: string }
    const { token, new_password } = body

    if (!token || token.length < 10) {
      return HttpResponse.json(
        { detail: 'Invalid or expired reset token' },
        { status: 400 }
      )
    }

    if (new_password.length < 8) {
      return HttpResponse.json(
        { detail: 'Password must be at least 8 characters' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      success: true,
      message: 'Password has been reset successfully.',
    })
  }),

  // Register (if enabled)
  http.post(`${API_BASE}/auth/register`, async ({ request }) => {
    await delay(150)

    const body = await request.json() as {
      username: string
      email: string
      password: string
      full_name?: string
    }

    if (!body.username || !body.email || !body.password) {
      return HttpResponse.json(
        { detail: 'Missing required fields' },
        { status: 400 }
      )
    }

    const newUser = userFactory.build({
      username: body.username,
      email: body.email,
      full_name: body.full_name || body.username,
      role: 'viewer', // Default role for new registrations
    })

    return HttpResponse.json({
      success: true,
      data: newUser,
    })
  }),
]

// Helper to reset auth state between tests
export const resetAuthState = (): void => {
  currentUser = null
  accessToken = null
}

// Helper to set authenticated state for tests
export const setAuthenticatedUser = (user: UserData, token: string): void => {
  currentUser = user
  accessToken = token
}

// Get current auth state (for assertions)
export const getAuthState = (): { user: UserData | null; token: string | null } => ({
  user: currentUser,
  token: accessToken,
})
