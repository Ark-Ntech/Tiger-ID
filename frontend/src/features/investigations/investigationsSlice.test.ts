import { describe, it, expect } from 'vitest'
import investigationsReducer, {
  setSelectedInvestigation,
  setFilters,
  clearFilters,
} from './investigationsSlice'
import type { Investigation } from '../../types'

describe('investigationsSlice', () => {
  const initialState = {
    selectedInvestigation: null,
    filters: {},
  }

  describe('initial state', () => {
    it('should return the initial state', () => {
      const state = investigationsReducer(undefined, { type: 'unknown' })

      expect(state.selectedInvestigation).toBeNull()
      expect(state.filters).toEqual({})
    })
  })

  describe('setSelectedInvestigation', () => {
    it('should set selected investigation', () => {
      const investigation: Investigation = {
        investigation_id: '123',
        title: 'Test Investigation',
        description: 'A test investigation',
        status: 'active',
        priority: 'high',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      const state = investigationsReducer(initialState, setSelectedInvestigation(investigation))

      expect(state.selectedInvestigation).toEqual(investigation)
    })

    it('should clear selected investigation when set to null', () => {
      const previousState = {
        selectedInvestigation: {
          investigation_id: '123',
          title: 'Test',
          description: 'Test',
          status: 'active',
          priority: 'high',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        filters: {},
      }

      const state = investigationsReducer(previousState, setSelectedInvestigation(null))

      expect(state.selectedInvestigation).toBeNull()
    })
  })

  describe('setFilters', () => {
    it('should set status filter', () => {
      const state = investigationsReducer(initialState, setFilters({ status: 'active' }))

      expect(state.filters.status).toBe('active')
    })

    it('should set priority filter', () => {
      const state = investigationsReducer(initialState, setFilters({ priority: 'high' }))

      expect(state.filters.priority).toBe('high')
    })

    it('should set search filter', () => {
      const state = investigationsReducer(initialState, setFilters({ search: 'tiger' }))

      expect(state.filters.search).toBe('tiger')
    })

    it('should merge multiple filters', () => {
      let state = investigationsReducer(initialState, setFilters({ status: 'active' }))
      state = investigationsReducer(state, setFilters({ priority: 'high' }))

      expect(state.filters.status).toBe('active')
      expect(state.filters.priority).toBe('high')
    })

    it('should set all filters at once', () => {
      const state = investigationsReducer(
        initialState,
        setFilters({
          status: 'completed',
          priority: 'critical',
          search: 'investigation',
        })
      )

      expect(state.filters.status).toBe('completed')
      expect(state.filters.priority).toBe('critical')
      expect(state.filters.search).toBe('investigation')
    })

    it('should update existing filter', () => {
      const previousState = {
        selectedInvestigation: null,
        filters: {
          status: 'active',
          priority: 'low',
        },
      }

      const state = investigationsReducer(previousState, setFilters({ status: 'completed' }))

      expect(state.filters.status).toBe('completed')
      expect(state.filters.priority).toBe('low') // Should be preserved
    })
  })

  describe('clearFilters', () => {
    it('should clear all filters', () => {
      const previousState = {
        selectedInvestigation: null,
        filters: {
          status: 'active',
          priority: 'high',
          search: 'test',
        },
      }

      const state = investigationsReducer(previousState, clearFilters())

      expect(state.filters).toEqual({})
    })

    it('should preserve selected investigation when clearing filters', () => {
      const investigation: Investigation = {
        investigation_id: '123',
        title: 'Test',
        description: 'Test',
        status: 'active',
        priority: 'high',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      const previousState = {
        selectedInvestigation: investigation,
        filters: {
          status: 'active',
        },
      }

      const state = investigationsReducer(previousState, clearFilters())

      expect(state.selectedInvestigation).toEqual(investigation)
      expect(state.filters).toEqual({})
    })

    it('should handle clearing already empty filters', () => {
      const state = investigationsReducer(initialState, clearFilters())

      expect(state.filters).toEqual({})
    })
  })

  describe('combined actions', () => {
    it('should handle filter and selection together', () => {
      const investigation: Investigation = {
        investigation_id: '456',
        title: 'Another Investigation',
        description: 'Description',
        status: 'completed',
        priority: 'medium',
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      let state = investigationsReducer(initialState, setFilters({ status: 'active' }))
      state = investigationsReducer(state, setSelectedInvestigation(investigation))

      expect(state.filters.status).toBe('active')
      expect(state.selectedInvestigation).toEqual(investigation)
    })
  })
})
