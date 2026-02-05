import { randomUUID } from 'crypto'

export interface UserData {
  id: string
  username: string
  email: string
  full_name: string
  role: 'admin' | 'analyst' | 'viewer'
  is_active: boolean
  created_at: string
}

export const userFactory = {
  build: (overrides: Partial<UserData> = {}): UserData => ({
    id: randomUUID(),
    username: `user_${Math.random().toString(36).substring(7)}`,
    email: `test_${Math.random().toString(36).substring(7)}@example.com`,
    full_name: 'Test User',
    role: 'analyst',
    is_active: true,
    created_at: new Date().toISOString(),
    ...overrides,
  }),

  buildAdmin: (overrides: Partial<UserData> = {}): UserData =>
    userFactory.build({ role: 'admin', ...overrides }),

  buildViewer: (overrides: Partial<UserData> = {}): UserData =>
    userFactory.build({ role: 'viewer', ...overrides }),

  buildInactive: (overrides: Partial<UserData> = {}): UserData =>
    userFactory.build({ is_active: false, ...overrides }),
}

// Test credentials for E2E tests
export const testCredentials = {
  admin: { username: 'admin', password: 'admin123' },
  analyst: { username: 'analyst', password: 'analyst123' },
  viewer: { username: 'viewer', password: 'viewer123' },
}
