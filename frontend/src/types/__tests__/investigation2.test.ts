import { describe, it, expect, expectTypeOf } from 'vitest'
import type {
  Investigation2Phase,
  Investigation2Status,
  Investigation2Response,
  TigerMatch,
  VerifiedCandidate,
  Investigation2Summary,
  ImageQuality,
} from '../investigation2'

describe('Investigation2 Type Safety', () => {
  describe('TigerMatch Type', () => {
    it('should have required fields properly typed', () => {
      const match: TigerMatch = {
        tiger_id: '123',
        tiger_name: 'Tiger A',
        similarity: 0.95,
        confidence: 0.9,
        model: 'wildlife_tools',
      }

      expectTypeOf(match.tiger_id).toBeString()
      expectTypeOf(match.tiger_name).toBeString()
      expectTypeOf(match.similarity).toBeNumber()
      expectTypeOf(match.confidence).toBeNumber()
      expectTypeOf(match.model).toBeString()
    })

    it('should not allow any type', () => {
      expectTypeOf<TigerMatch>().not.toBeAny()
    })
  })

  describe('VerifiedCandidate Type', () => {
    it('should extend TigerMatch with verification fields', () => {
      const candidate: VerifiedCandidate = {
        tiger_id: '123',
        tiger_name: 'Tiger A',
        similarity: 0.95,
        confidence: 0.9,
        model: 'wildlife_tools',
        num_matches: 50,
        match_score: 0.88,
        normalized_match_score: 0.92,
        combined_score: 0.935,
        verification_status: 'verified',
      }

      expectTypeOf(candidate.num_matches).toBeNumber()
      expectTypeOf(candidate.verification_status).toBeString()
    })

    it('should not allow any type', () => {
      expectTypeOf<VerifiedCandidate>().not.toBeAny()
    })
  })

  describe('Investigation2Response Type', () => {
    it('should have properly typed required fields', () => {
      const response: Investigation2Response = {
        investigation_id: 'inv-123',
        status: 'completed',
        started_at: '2026-02-05T10:00:00Z',
        steps: [],
      }

      expectTypeOf(response.investigation_id).toBeString()
      expectTypeOf(response.steps).toBeArray()
    })

    it('should not allow any type', () => {
      expectTypeOf<Investigation2Response>().not.toBeAny()
    })
  })

  describe('No Any Types Allowed', () => {
    it('should reject any type in TigerMatch array', () => {
      const matches: TigerMatch[] = []
      expectTypeOf(matches).not.toBeAny()
    })

    it('should reject any type in Investigation2Response', () => {
      expectTypeOf<Investigation2Response>().not.toBeAny()
    })
  })
})
