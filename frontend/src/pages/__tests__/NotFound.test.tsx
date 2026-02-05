import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import React from 'react'
import NotFound from '../NotFound'

const renderNotFound = () => {
  return render(
    <BrowserRouter>
      <NotFound />
    </BrowserRouter>
  )
}

describe('NotFound', () => {
  describe('rendering', () => {
    it('should render 404 text', () => {
      renderNotFound()

      expect(screen.getByText('404')).toBeInTheDocument()
    })

    it('should render page not found heading', () => {
      renderNotFound()

      expect(screen.getByText('Page Not Found')).toBeInTheDocument()
    })

    it('should render helpful message', () => {
      renderNotFound()

      expect(screen.getByText(/page you're looking for/i)).toBeInTheDocument()
    })

    it('should render go home button', () => {
      renderNotFound()

      expect(screen.getByRole('link', { name: /go home/i })).toBeInTheDocument()
    })
  })

  describe('navigation', () => {
    it('should have home link pointing to root', () => {
      renderNotFound()

      const homeLink = screen.getByRole('link', { name: /go home/i })
      expect(homeLink).toHaveAttribute('href', '/')
    })
  })

  describe('styling', () => {
    it('should have large 404 text', () => {
      renderNotFound()

      const heading = screen.getByText('404')
      expect(heading).toHaveClass('text-9xl')
    })

    it('should center content', () => {
      const { container } = renderNotFound()

      const wrapper = container.firstChild
      expect(wrapper).toHaveClass('flex')
      expect(wrapper).toHaveClass('items-center')
      expect(wrapper).toHaveClass('justify-center')
    })
  })
})
