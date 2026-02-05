import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { Investigation2Methodology } from '../Investigation2Methodology'

const mockMethodology = {
  phases: [
    {
      name: 'Image Upload & Analysis',
      description: 'Initial image processing and quality assessment',
      tools_used: ['OpenCV', 'EXIF Parser'],
      status: 'completed' as const,
      duration_ms: 1500,
    },
    {
      name: 'Tiger Detection',
      description: 'MegaDetector v5 object detection',
      tools_used: ['MegaDetector'],
      status: 'completed' as const,
      duration_ms: 3200,
    },
    {
      name: 'ReID Analysis',
      description: '6-model ensemble stripe analysis',
      tools_used: ['Wildlife Tools', 'CVWC2019', 'TransReID'],
      status: 'running' as const,
    },
  ],
  reasoning_steps: [
    {
      step: 1,
      thought: 'Processing input image',
      action: 'Running quality assessment',
      observation: 'Image quality is good',
    },
    {
      step: 2,
      thought: 'Detecting tigers',
      action: 'Running MegaDetector',
      observation: 'Found 1 tiger',
    },
  ],
}

describe('Investigation2Methodology', () => {
  it('renders methodology section', () => {
    render(<Investigation2Methodology methodology={mockMethodology} />)
    expect(screen.getByText(/Methodology/i)).toBeInTheDocument()
  })

  it('displays phase names', () => {
    render(<Investigation2Methodology methodology={mockMethodology} />)
    expect(screen.getByText('Image Upload & Analysis')).toBeInTheDocument()
    expect(screen.getByText('Tiger Detection')).toBeInTheDocument()
    expect(screen.getByText('ReID Analysis')).toBeInTheDocument()
  })

  it('shows tools used in phases', () => {
    render(<Investigation2Methodology methodology={mockMethodology} />)
    expect(screen.getByText(/OpenCV/)).toBeInTheDocument()
    expect(screen.getByText(/MegaDetector/)).toBeInTheDocument()
  })

  it('handles empty methodology gracefully', () => {
    render(<Investigation2Methodology methodology={{ phases: [], reasoning_steps: [] }} />)
    expect(screen.getByText(/Methodology/i)).toBeInTheDocument()
  })

  it('handles undefined methodology', () => {
    render(<Investigation2Methodology methodology={undefined} />)
    // Should render without crashing
    expect(document.body).toBeInTheDocument()
  })

  it('displays phase descriptions', () => {
    render(<Investigation2Methodology methodology={mockMethodology} />)
    expect(screen.getByText(/Initial image processing/)).toBeInTheDocument()
    expect(screen.getByText(/MegaDetector v5/)).toBeInTheDocument()
  })

  it('shows duration for completed phases', () => {
    render(<Investigation2Methodology methodology={mockMethodology} />)
    // 1500ms = 1.5s
    expect(screen.getByText(/1\.5s|1500ms/i)).toBeInTheDocument()
  })
})
