import { setupServer } from 'msw/node'
import {
  handlers,
  resetAuthState,
  resetTigersState,
  resetInvestigationsState,
} from './handlers'

export const server = setupServer(...handlers)

// Reset all mocks between tests
export const resetMocks = (): void => {
  resetAuthState()
  resetTigersState()
  resetInvestigationsState()
  server.resetHandlers()
}

export { handlers }
