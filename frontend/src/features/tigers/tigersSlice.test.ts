import { describe, it, expect } from 'vitest'
import tigersReducer, {
  setSelectedTiger,
  setFilters,
  clearFilters,
} from './tigersSlice'
import type { Tiger } from '../../types'

describe('tigersSlice', () => {
  const initialState = {
    selectedTiger: null,
    filters: {},
  }

  describe('initial state', () => {
    it('should return the initial state', () => {
      const state = tigersReducer(undefined, { type: 'unknown' })

      expect(state.selectedTiger).toBeNull()
      expect(state.filters).toEqual({})
    })
  })

  describe('setSelectedTiger', () => {
    it('should set selected tiger', () => {
      const tiger: Tiger = {
        id: 'tiger-123',
        name: 'Raja',
        estimated_age: 5,
        sex: 'male',
        first_seen: '2023-01-01',
        last_seen: '2024-01-01',
        confidence_score: 0.95,
        images: [],
        locations: [],
      }

      const state = tigersReducer(initialState, setSelectedTiger(tiger))

      expect(state.selectedTiger).toEqual(tiger)
    })

    it('should clear selected tiger when set to null', () => {
      const previousState = {
        selectedTiger: {
          id: 'tiger-123',
          name: 'Raja',
          estimated_age: 5,
          sex: 'male',
          first_seen: '2023-01-01',
          confidence_score: 0.95,
          images: [],
          locations: [],
        },
        filters: {},
      }

      const state = tigersReducer(previousState, setSelectedTiger(null))

      expect(state.selectedTiger).toBeNull()
    })

    it('should replace existing selected tiger', () => {
      const tiger1: Tiger = {
        id: 'tiger-1',
        name: 'Raja',
        estimated_age: 5,
        sex: 'male',
        first_seen: '2023-01-01',
        confidence_score: 0.95,
        images: [],
        locations: [],
      }

      const tiger2: Tiger = {
        id: 'tiger-2',
        name: 'Sher',
        estimated_age: 7,
        sex: 'male',
        first_seen: '2022-01-01',
        confidence_score: 0.88,
        images: [],
        locations: [],
      }

      let state = tigersReducer(initialState, setSelectedTiger(tiger1))
      expect(state.selectedTiger?.name).toBe('Raja')

      state = tigersReducer(state, setSelectedTiger(tiger2))
      expect(state.selectedTiger?.name).toBe('Sher')
    })
  })

  describe('setFilters', () => {
    it('should set search filter', () => {
      const state = tigersReducer(initialState, setFilters({ search: 'raja' }))

      expect(state.filters.search).toBe('raja')
    })

    it('should update existing search filter', () => {
      const previousState = {
        selectedTiger: null,
        filters: {
          search: 'raja',
        },
      }

      const state = tigersReducer(previousState, setFilters({ search: 'sher' }))

      expect(state.filters.search).toBe('sher')
    })

    it('should merge filters with existing state', () => {
      const previousState = {
        selectedTiger: null,
        filters: {
          search: 'existing',
        },
      }

      const state = tigersReducer(previousState, setFilters({ search: 'new' }))

      expect(state.filters.search).toBe('new')
    })

    it('should handle empty search filter', () => {
      const state = tigersReducer(initialState, setFilters({ search: '' }))

      expect(state.filters.search).toBe('')
    })
  })

  describe('clearFilters', () => {
    it('should clear all filters', () => {
      const previousState = {
        selectedTiger: null,
        filters: {
          search: 'test search',
        },
      }

      const state = tigersReducer(previousState, clearFilters())

      expect(state.filters).toEqual({})
    })

    it('should preserve selected tiger when clearing filters', () => {
      const tiger: Tiger = {
        id: 'tiger-123',
        name: 'Raja',
        estimated_age: 5,
        sex: 'male',
        first_seen: '2023-01-01',
        confidence_score: 0.95,
        images: [],
        locations: [],
      }

      const previousState = {
        selectedTiger: tiger,
        filters: {
          search: 'test',
        },
      }

      const state = tigersReducer(previousState, clearFilters())

      expect(state.selectedTiger).toEqual(tiger)
      expect(state.filters).toEqual({})
    })

    it('should handle clearing already empty filters', () => {
      const state = tigersReducer(initialState, clearFilters())

      expect(state.filters).toEqual({})
    })
  })

  describe('combined actions', () => {
    it('should handle filter and selection together', () => {
      const tiger: Tiger = {
        id: 'tiger-456',
        name: 'Bagheera',
        estimated_age: 8,
        sex: 'female',
        first_seen: '2022-06-15',
        confidence_score: 0.92,
        images: [],
        locations: [],
      }

      let state = tigersReducer(initialState, setFilters({ search: 'tiger' }))
      state = tigersReducer(state, setSelectedTiger(tiger))

      expect(state.filters.search).toBe('tiger')
      expect(state.selectedTiger).toEqual(tiger)
    })

    it('should clear filters independently of selection', () => {
      const tiger: Tiger = {
        id: 'tiger-789',
        name: 'Simba',
        estimated_age: 3,
        sex: 'male',
        first_seen: '2024-01-01',
        confidence_score: 0.98,
        images: [],
        locations: [],
      }

      let state = tigersReducer(initialState, setSelectedTiger(tiger))
      state = tigersReducer(state, setFilters({ search: 'test' }))
      state = tigersReducer(state, clearFilters())

      expect(state.filters).toEqual({})
      expect(state.selectedTiger).toEqual(tiger)
    })
  })
})
