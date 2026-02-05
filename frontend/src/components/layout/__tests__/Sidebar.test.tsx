import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import React from 'react'
import Sidebar from '../Sidebar'

// Mock cn utility
vi.mock('../../../utils/cn', () => ({
  cn: (...classes: (string | undefined | null | false)[]) =>
    classes.filter(Boolean).join(' '),
}))

// Mock heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  HomeIcon: () => <span data-testid="home-icon">HomeIcon</span>,
  MagnifyingGlassCircleIcon: () => <span data-testid="search-icon">SearchIcon</span>,
  FolderIcon: () => <span data-testid="folder-icon">FolderIcon</span>,
  ShieldCheckIcon: () => <span data-testid="shield-icon">ShieldIcon</span>,
  BuildingOfficeIcon: () => <span data-testid="building-icon">BuildingIcon</span>,
  ChartBarIcon: () => <span data-testid="chart-icon">ChartIcon</span>,
  SparklesIcon: () => <span data-testid="sparkles-icon">SparklesIcon</span>,
}))

const renderSidebar = (initialPath = '/') => {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Sidebar />
    </MemoryRouter>
  )
}

describe('Sidebar', () => {
  describe('rendering', () => {
    it('should render sidebar', () => {
      const { container } = renderSidebar()

      expect(container.querySelector('aside')).toBeInTheDocument()
    })

    it('should render Tiger ID logo section', () => {
      renderSidebar()

      expect(screen.getByText('Tiger ID')).toBeInTheDocument()
    })

    it('should render Investigation System subtitle', () => {
      renderSidebar()

      expect(screen.getByText('Investigation System')).toBeInTheDocument()
    })

    it('should render tiger emoji', () => {
      renderSidebar()

      expect(screen.getByText('🐅')).toBeInTheDocument()
    })
  })

  describe('navigation items', () => {
    it('should render Home link', () => {
      renderSidebar()

      expect(screen.getByText('Home')).toBeInTheDocument()
    })

    it('should render Dashboard link', () => {
      renderSidebar()

      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })

    it('should render Investigations link', () => {
      renderSidebar()

      expect(screen.getByText('Investigations')).toBeInTheDocument()
    })

    it('should render Launch Investigation link', () => {
      renderSidebar()

      expect(screen.getByText('Launch Investigation')).toBeInTheDocument()
    })

    it('should render Investigation 2.0 link', () => {
      renderSidebar()

      expect(screen.getByText('Investigation 2.0')).toBeInTheDocument()
    })

    it('should render Tigers link', () => {
      renderSidebar()

      expect(screen.getByText('Tigers')).toBeInTheDocument()
    })

    it('should render Facilities link', () => {
      renderSidebar()

      expect(screen.getByText('Facilities')).toBeInTheDocument()
    })

    it('should render Verification link', () => {
      renderSidebar()

      expect(screen.getByText('Verification')).toBeInTheDocument()
    })
  })

  describe('navigation links', () => {
    it('should have correct href for Home', () => {
      renderSidebar()

      const link = screen.getByText('Home').closest('a')
      expect(link).toHaveAttribute('href', '/')
    })

    it('should have correct href for Dashboard', () => {
      renderSidebar()

      const link = screen.getByText('Dashboard').closest('a')
      expect(link).toHaveAttribute('href', '/dashboard')
    })

    it('should have correct href for Investigations', () => {
      renderSidebar()

      const link = screen.getByText('Investigations').closest('a')
      expect(link).toHaveAttribute('href', '/investigations')
    })

    it('should have correct href for Tigers', () => {
      renderSidebar()

      const link = screen.getByText('Tigers').closest('a')
      expect(link).toHaveAttribute('href', '/tigers')
    })

    it('should have correct href for Facilities', () => {
      renderSidebar()

      const link = screen.getByText('Facilities').closest('a')
      expect(link).toHaveAttribute('href', '/facilities')
    })

    it('should have correct href for Investigation 2.0', () => {
      renderSidebar()

      const link = screen.getByText('Investigation 2.0').closest('a')
      expect(link).toHaveAttribute('href', '/investigation2')
    })
  })

  describe('active state', () => {
    it('should highlight Home link when on root path', () => {
      renderSidebar('/')

      const homeLink = screen.getByText('Home').closest('a')
      expect(homeLink).toHaveClass('bg-primary-600')
    })

    it('should highlight Dashboard link when on dashboard path', () => {
      renderSidebar('/dashboard')

      const dashboardLink = screen.getByText('Dashboard').closest('a')
      expect(dashboardLink).toHaveClass('bg-primary-600')
    })

    it('should highlight Tigers link when on tigers path', () => {
      renderSidebar('/tigers')

      const tigersLink = screen.getByText('Tigers').closest('a')
      expect(tigersLink).toHaveClass('bg-primary-600')
    })
  })

  describe('footer', () => {
    it('should render version info', () => {
      renderSidebar()

      expect(screen.getByText('Version 1.0.0')).toBeInTheDocument()
    })

    it('should render copyright', () => {
      renderSidebar()

      expect(screen.getByText('© 2024 Tiger ID')).toBeInTheDocument()
    })
  })

  describe('styling', () => {
    it('should have dark background', () => {
      const { container } = renderSidebar()

      const aside = container.querySelector('aside')
      expect(aside).toHaveClass('bg-gray-900')
    })

    it('should have white text', () => {
      const { container } = renderSidebar()

      const aside = container.querySelector('aside')
      expect(aside).toHaveClass('text-white')
    })

    it('should have fixed width', () => {
      const { container } = renderSidebar()

      const aside = container.querySelector('aside')
      expect(aside).toHaveClass('w-64')
    })

    it('should have min height screen', () => {
      const { container } = renderSidebar()

      const aside = container.querySelector('aside')
      expect(aside).toHaveClass('min-h-screen')
    })

    it('should have flex column layout', () => {
      const { container } = renderSidebar()

      const aside = container.querySelector('aside')
      expect(aside).toHaveClass('flex')
      expect(aside).toHaveClass('flex-col')
    })
  })

  describe('icons', () => {
    it('should render navigation icons', () => {
      renderSidebar()

      // Check that icons are rendered (mocked)
      expect(screen.getByTestId('home-icon')).toBeInTheDocument()
      expect(screen.getByTestId('chart-icon')).toBeInTheDocument()
      expect(screen.getByTestId('folder-icon')).toBeInTheDocument()
    })
  })
})
