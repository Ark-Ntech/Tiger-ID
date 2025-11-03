import { useAppDispatch, useAppSelector } from '../app/hooks'
import { login as loginAction, logout as logoutAction, register as registerAction } from '../features/auth/authSlice'
import type { LoginCredentials } from '../types'

export const useAuth = () => {
  const dispatch = useAppDispatch()
  const { user, isAuthenticated, loading, error } = useAppSelector((state) => state.auth)

  const login = async (credentials: LoginCredentials) => {
    return dispatch(loginAction(credentials)).unwrap()
  }

  const logout = async () => {
    return dispatch(logoutAction()).unwrap()
  }

  const register = async (data: {
    username: string
    email: string
    password: string
    full_name?: string
  }) => {
    return dispatch(registerAction(data)).unwrap()
  }

  return {
    user,
    isAuthenticated,
    loading,
    error,
    login,
    logout,
    register,
  }
}

