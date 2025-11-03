import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { Tiger } from '../../types'

interface TigersState {
  selectedTiger: Tiger | null
  filters: {
    search?: string
  }
}

const initialState: TigersState = {
  selectedTiger: null,
  filters: {},
}

const tigersSlice = createSlice({
  name: 'tigers',
  initialState,
  reducers: {
    setSelectedTiger: (state, action: PayloadAction<Tiger | null>) => {
      state.selectedTiger = action.payload
    },
    setFilters: (state, action: PayloadAction<{ search?: string }>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearFilters: (state) => {
      state.filters = {}
    },
  },
})

export const { setSelectedTiger, setFilters, clearFilters } = tigersSlice.actions
export default tigersSlice.reducer

