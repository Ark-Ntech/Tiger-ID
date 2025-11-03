import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { Investigation } from '../../types'

interface InvestigationsState {
  selectedInvestigation: Investigation | null
  filters: {
    status?: string
    priority?: string
    search?: string
  }
}

const initialState: InvestigationsState = {
  selectedInvestigation: null,
  filters: {},
}

const investigationsSlice = createSlice({
  name: 'investigations',
  initialState,
  reducers: {
    setSelectedInvestigation: (state, action: PayloadAction<Investigation | null>) => {
      state.selectedInvestigation = action.payload
    },
    setFilters: (
      state,
      action: PayloadAction<{
        status?: string
        priority?: string
        search?: string
      }>
    ) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearFilters: (state) => {
      state.filters = {}
    },
  },
})

export const { setSelectedInvestigation, setFilters, clearFilters } =
  investigationsSlice.actions
export default investigationsSlice.reducer

