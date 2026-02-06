import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import Layout from '../Layout'

// Mock cn utility
vi.mock('../../../utils/cn', () => ({
  cn: (...classes: (string | undefined | null | false)[]) =>
    classes.filter(Boolean).join(' '),
}))

// Mock Sidebar
vi.mock('../Sidebar', () => ({
  default: () => <div data-testid="sidebar">Sidebar</div>,
}))

// Mock Header
vi.mock('../Header', () => ({
  default: () => <div data-testid="header">Header</div>,
}))

const createMockStore = () => {
  return configureStore({
    reducer: {
      auth: () => ({ token: 'test-token', user: { id: '1', username: 'test' } }),
      notifications: () => ({ notifications: [], unreadCount: 0 }),
    },
  })
}

const renderLayout = (initialRoute = '/') => {
  return render(
    <Provider store={createMockStore()}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<div data-testid="home-content">Home Content</div>} />
            <Route path="dashboard" element={<div data-testid="dashboard-content">Dashboard Content</div>} />
            <Route path="investigations" element={<div data-testid="investigations-content">Investigations Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </Provider>
  )
}

describe('Layout', () => {
  describe('rendering', () => {
    it('should render layout container', () => {
      const { container } = renderLayout()

      expect(container.firstChild).toBeInTheDocument()
    })

    it('should render sidebar', () => {
      renderLayout()

      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    })

    it('should render header', () => {
      renderLayout()

      expect(screen.getByTestId('header')).toBeInTheDocument()
    })

    it('should render main content area', () => {
      renderLayout()

      const main = document.querySelector('main')
      expect(main).toBeInTheDocument()
    })
  })

  describe('routing', () => {
    it('should render home content at root path', () => {
      renderLayout('/')

      expect(screen.getByTestId('home-content')).toBeInTheDocument()
    })

    it('should render dashboard content at /dashboard', () => {
      renderLayout('/dashboard')

      expect(screen.getByTestId('dashboard-content')).toBeInTheDocument()
    })

    it('should render investigations content at /investigations', () => {
      renderLayout('/investigations')

      expect(screen.getByTestId('investigations-content')).toBeInTheDocument()
    })
  })

  describe('layout structure', () => {
    it('should have flex container for sidebar and main content', () => {
      const { container } = renderLayout()

      expect(container.firstChild).toHaveClass('flex')
    })

    it('should have full height', () => {
      const { container } = renderLayout()

      expect(container.firstChild).toHaveClass('h-screen')
    })

    it('should have overflow hidden', () => {
      const { container } = renderLayout()

      expect(container.firstChild).toHaveClass('overflow-hidden')
    })
  })

  describe('dark mode styles', () => {
    it('should have light mode background', () => {
      const { container } = renderLayout()

      expect(container.firstChild).toHaveClass('bg-tactical-50')
    })

    it('should have dark mode background class', () => {
      const { container } = renderLayout()

      expect(container.firstChild).toHaveClass('dark:bg-tactical-950')
    })

    it('should have transition on colors', () => {
      const { container } = renderLayout()

      expect(container.firstChild).toHaveClass('transition-colors')
    })
  })

  describe('main content area', () => {
    it('should have padding', () => {
      renderLayout()

      const main = document.querySelector('main')
      expect(main).toHaveClass('p-6')
    })

    it('should have overflow-y-auto for scrolling', () => {
      renderLayout()

      const main = document.querySelector('main')
      expect(main).toHaveClass('overflow-y-auto')
    })

    it('should be flex-1 to fill remaining space', () => {
      renderLayout()

      const main = document.querySelector('main')
      expect(main).toHaveClass('flex-1')
    })
  })
})
