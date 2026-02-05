import { authHandlers, resetAuthState, setAuthenticatedUser, getAuthState } from './auth.handlers'
import { tigersHandlers, resetTigersState, setTigers, getTigers } from './tigers.handlers'
import { investigationsHandlers, resetInvestigationsState, setInvestigations, getInvestigations } from './investigations.handlers'

export const handlers = [
  ...authHandlers,
  ...tigersHandlers,
  ...investigationsHandlers,
]

export {
  // Auth
  resetAuthState,
  setAuthenticatedUser,
  getAuthState,
  // Tigers
  resetTigersState,
  setTigers,
  getTigers,
  // Investigations
  resetInvestigationsState,
  setInvestigations,
  getInvestigations,
}
