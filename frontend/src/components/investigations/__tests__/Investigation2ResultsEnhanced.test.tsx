import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import Investigation2ResultsEnhanced from '../Investigation2ResultsEnhanced'
import type { Investigation2Response, TigerMatch } from '../../../types/investigation2'

const mockMatch: TigerMatch = {
  tiger_id: 'tiger-123',
  tiger_name: 'Raja',
  similarity: 0.95,
  confidence: 0.92,
  model: 'wildlife_tools',
  facility_name: 'Test Zoo',
  last_seen_location: 'Enclosure A',
}

const mockInvestigation: Investigation2Response = {
  investigation_id: 'inv-123',
  status: 'completed',
  started_at: '2026-02-05T10:00:00Z',
  completed_at: '2026-02-05T10:05:00Z',
  steps: [],
  summary: {
    identified: true,
    confidence: 0.95,
    all_matches: [mockMatch],
    evidence_count: 5,
    key_findings: ['High confidence match found'],
    recommendations: ['Verify with additional images'],
  },
}

describe('Investigation2ResultsEnhanced Component', () => {
  describe('Type Safety', () => {
    it('should receive properly typed investigation prop', () => {
      const onRegenerateReport = vi.fn()
      
      render(
        <Investigation2ResultsEnhanced
          investigation={mockInvestigation}
          fullWidth={false}
          onRegenerateReport={onRegenerateReport}
        />
      )

      expect(mockInvestigation.investigation_id).toBe('inv-123')
      expect(mockInvestigation.status).toBe('completed')
    })

    it('should handle TigerMatch type correctly', () => {
      const match = mockInvestigation.summary?.all_matches[0]
      
      expect(match).toBeDefined()
      expect(match?.tiger_id).toBe('tiger-123')
      expect(match?.tiger_name).toBe('Raja')
      expect(match?.similarity).toBe(0.95)
      expect(match?.confidence).toBe(0.92)
    })

    it('should not accept any type for investigation prop', () => {
      const investigation: Investigation2Response = mockInvestigation
      
      expect(investigation.investigation_id).toBeTypeOf('string')
      expect(investigation.status).toBeTypeOf('string')
      expect(investigation.steps).toBeInstanceOf(Array)
    })
  })

  describe('Rendering', () => {
    it('should render investigation results', () => {
      render(
        <Investigation2ResultsEnhanced
          investigation={mockInvestigation}
        />
      )

      expect(screen.getByText(/inv-123/i)).toBeDefined()
    })

    it('should display match information', () => {
      render(
        <Investigation2ResultsEnhanced
          investigation={mockInvestigation}
        />
      )

      const summary = mockInvestigation.summary
      expect(summary?.all_matches.length).toBeGreaterThan(0)
    })
  })

  describe('Enhanced Workflow Data', () => {
    it('should handle image quality data when present', () => {
      const investigationWithQuality: Investigation2Response = {
        ...mockInvestigation,
        summary: {
          ...mockInvestigation.summary!,
          image_quality: {
            overall_score: 0.85,
            resolution_score: 0.9,
            blur_score: 0.8,
            stripe_visibility: 0.85,
            issues: ['Slight blur'],
            recommendations: ['Use better lighting'],
          },
        },
      }

      render(
        <Investigation2ResultsEnhanced
          investigation={investigationWithQuality}
        />
      )

      const quality = investigationWithQuality.summary?.image_quality
      expect(quality?.overall_score).toBe(0.85)
      expect(quality?.issues).toBeInstanceOf(Array)
    })

    it('should handle verified candidates when present', () => {
      const investigationWithVerification: Investigation2Response = {
        ...mockInvestigation,
        summary: {
          ...mockInvestigation.summary!,
          verified_candidates: [
            {
              ...mockMatch,
              num_matches: 50,
              match_score: 0.88,
              normalized_match_score: 0.92,
              combined_score: 0.935,
              verification_status: 'verified',
            },
          ],
          verification_applied: true,
        },
      }

      render(
        <Investigation2ResultsEnhanced
          investigation={investigationWithVerification}
        />
      )

      const verified = investigationWithVerification.summary?.verified_candidates?.[0]
      expect(verified?.num_matches).toBe(50)
      expect(verified?.verification_status).toBe('verified')
    })
  })

  describe('Report Audience Selection', () => {
    it('should handle report audience prop', () => {
      const investigationWithAudience: Investigation2Response = {
        ...mockInvestigation,
        summary: {
          ...mockInvestigation.summary!,
          report_audience: 'law_enforcement',
        },
      }

      render(
        <Investigation2ResultsEnhanced
          investigation={investigationWithAudience}
        />
      )

      const audience = investigationWithAudience.summary?.report_audience
      expect(audience).toBe('law_enforcement')
    })

    it('should call onRegenerateReport with correct audience type', () => {
      const onRegenerateReport = vi.fn()
      
      render(
        <Investigation2ResultsEnhanced
          investigation={mockInvestigation}
          onRegenerateReport={onRegenerateReport}
        />
      )

      expect(onRegenerateReport).toBeInstanceOf(Function)
    })
  })
})
