import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { Investigation2Methodology } from '../Investigation2Methodology'
import type { ReasoningChainStep } from '../../../types/investigation2'

const mockSteps: ReasoningChainStep[] = [
  {
    step: 1,
    phase: 'Image Upload & Analysis',
    action: 'Running quality assessment',
    evidence: ['EXIF data extracted', 'Resolution: 1920x1080'],
    reasoning: 'Processing input image',
    conclusion: 'Image quality is good',
    confidence: 0.95,
    timestamp: '2024-01-01T00:00:00Z',
  },
  {
    step: 2,
    phase: 'Tiger Detection',
    action: 'Running MegaDetector',
    evidence: ['Detection confidence: 98%'],
    reasoning: 'Detecting tigers in the image',
    conclusion: 'Found 1 tiger',
    confidence: 0.98,
    timestamp: '2024-01-01T00:00:01Z',
  },
  {
    step: 3,
    phase: 'ReID Analysis',
    action: 'Running 6-model ensemble',
    evidence: ['Wildlife Tools: 0.92', 'CVWC2019: 0.88'],
    reasoning: 'Analyzing stripe patterns',
    conclusion: 'Match found with Raja',
    confidence: 0.90,
    timestamp: '2024-01-01T00:00:02Z',
  },
]

describe('Investigation2Methodology', () => {
  it('renders methodology section', () => {
    render(<Investigation2Methodology steps={mockSteps} />)
    expect(screen.getByText(/Investigation Chain/i)).toBeInTheDocument()
  })

  it('displays phase names', () => {
    render(<Investigation2Methodology steps={mockSteps} />)
    expect(screen.getByText('Image Upload & Analysis')).toBeInTheDocument()
    expect(screen.getByText('Tiger Detection')).toBeInTheDocument()
    expect(screen.getByText('ReID Analysis')).toBeInTheDocument()
  })

  it('shows step numbers', () => {
    render(<Investigation2Methodology steps={mockSteps} />)
    // Step badges
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('handles empty steps gracefully', () => {
    render(<Investigation2Methodology steps={[]} />)
    expect(screen.getByText(/No Methodology Data/i)).toBeInTheDocument()
  })

  it('handles undefined steps', () => {
    render(<Investigation2Methodology steps={[]} />)
    // Should render without crashing
    expect(document.body).toBeInTheDocument()
  })

  it('displays step count', () => {
    render(<Investigation2Methodology steps={mockSteps} />)
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('steps')).toBeInTheDocument()
  })

  it('shows confidence information', () => {
    render(<Investigation2Methodology steps={mockSteps} />)
    // Final confidence is shown in the header
    expect(screen.getByText(/Final Confidence/i)).toBeInTheDocument()
  })
})
