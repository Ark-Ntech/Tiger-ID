import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import axios from 'axios'
import type { User, LoginCredentials, AuthResponse } from '../../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
}

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  loading: false,
  error: null,
}

// Async thunks
export const login = createAsyncThunk<AuthResponse, LoginCredentials>(
  'auth/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await axios.post(`${API_URL}/api/auth/login`, credentials)
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Login failed')
    }
  }
)

export const logout = createAsyncThunk('auth/logout', async () => {
  try {
    await axios.post(`${API_URL}/api/auth/logout`)
  } catch (error) {
    // Logout locally even if API call fails
    console.error('Logout error:', error)
  }
})

export const register = createAsyncThunk<
  AuthResponse,
  {
    username: string
    email: string
    password: string
    full_name?: string
  }
>('auth/register', async (data, { rejectWithValue }) => {
  try {
    const response = await axios.post(`${API_URL}/api/auth/register`, data)
    return response.data
  } catch (error: any) {
    return rejectWithValue(error.response?.data?.message || 'Registration failed')
  }
})

export const requestPasswordReset = createAsyncThunk<void, string>(
  'auth/requestPasswordReset',
  async (email, { rejectWithValue }) => {
    try {
      await axios.post(`${API_URL}/api/auth/password-reset/request`, { email })
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Password reset request failed')
    }
  }
)

export const confirmPasswordReset = createAsyncThunk<
  void,
  { token: string; new_password: string }
>('auth/confirmPasswordReset', async (data, { rejectWithValue }) => {
  try {
    await axios.post(`${API_URL}/api/auth/password-reset/confirm`, data)
  } catch (error: any) {
    return rejectWithValue(error.response?.data?.message || 'Password reset failed')
  }
})

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false
        state.isAuthenticated = true
        state.user = action.payload.user
        state.token = action.payload.access_token
        localStorage.setItem('token', action.payload.access_token)
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null
        state.token = null
        state.isAuthenticated = false
        localStorage.removeItem('token')
      })
      // Register
      .addCase(register.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(register.fulfilled, (state, action) => {
        state.loading = false
        state.isAuthenticated = true
        state.user = action.payload.user
        state.token = action.payload.access_token
        localStorage.setItem('token', action.payload.access_token)
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      // Password reset request
      .addCase(requestPasswordReset.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(requestPasswordReset.fulfilled, (state) => {
        state.loading = false
      })
      .addCase(requestPasswordReset.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      // Password reset confirm
      .addCase(confirmPasswordReset.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(confirmPasswordReset.fulfilled, (state) => {
        state.loading = false
      })
      .addCase(confirmPasswordReset.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
  },
})

export const { clearError, setUser } = authSlice.actions
export default authSlice.reducer

