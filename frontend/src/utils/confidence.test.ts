import { describe, it, expect } from 'vitest'
import {
  CONFIDENCE_THRESHOLDS,
  getConfidenceLevel,
  normalizeScore,
  toPercentage,
  getConfidenceColors,
  getConfidenceColorsFromScore,
  getModelInfo,
  getVerificationColors,
  CONFIDENCE_COLORS,
  MODEL_COLORS,
} from './confidence'

describe('confidence utils', () => {
  describe('CONFIDENCE_THRESHOLDS', () => {
    it('should have correct threshold values', () => {
      expect(CONFIDENCE_THRESHOLDS.HIGH).toBe(0.85)
      expect(CONFIDENCE_THRESHOLDS.MEDIUM).toBe(0.65)
      expect(CONFIDENCE_THRESHOLDS.LOW).toBe(0.4)
    })
  })

  describe('getConfidenceLevel', () => {
    it('should return high for scores >= 0.85', () => {
      expect(getConfidenceLevel(0.85)).toBe('high')
      expect(getConfidenceLevel(0.90)).toBe('high')
      expect(getConfidenceLevel(1.0)).toBe('high')
    })

    it('should return medium for scores >= 0.65 and < 0.85', () => {
      expect(getConfidenceLevel(0.65)).toBe('medium')
      expect(getConfidenceLevel(0.70)).toBe('medium')
      expect(getConfidenceLevel(0.84)).toBe('medium')
    })

    it('should return low for scores >= 0.4 and < 0.65', () => {
      expect(getConfidenceLevel(0.40)).toBe('low')
      expect(getConfidenceLevel(0.50)).toBe('low')
      expect(getConfidenceLevel(0.64)).toBe('low')
    })

    it('should return critical for scores < 0.4', () => {
      expect(getConfidenceLevel(0.39)).toBe('critical')
      expect(getConfidenceLevel(0.20)).toBe('critical')
      expect(getConfidenceLevel(0.0)).toBe('critical')
    })

    it('should normalize scores > 1 (percentage format)', () => {
      expect(getConfidenceLevel(85)).toBe('high')
      expect(getConfidenceLevel(70)).toBe('medium')
      expect(getConfidenceLevel(50)).toBe('low')
      expect(getConfidenceLevel(30)).toBe('critical')
    })

    it('should handle boundary values', () => {
      expect(getConfidenceLevel(0.85)).toBe('high')
      expect(getConfidenceLevel(0.849999)).toBe('medium')
      expect(getConfidenceLevel(0.65)).toBe('medium')
      expect(getConfidenceLevel(0.649999)).toBe('low')
      expect(getConfidenceLevel(0.4)).toBe('low')
      expect(getConfidenceLevel(0.399999)).toBe('critical')
    })
  })

  describe('normalizeScore', () => {
    it('should return scores <= 1 unchanged', () => {
      expect(normalizeScore(0.5)).toBe(0.5)
      expect(normalizeScore(1.0)).toBe(1.0)
      expect(normalizeScore(0)).toBe(0)
    })

    it('should convert percentage scores to 0-1 range', () => {
      expect(normalizeScore(50)).toBe(0.5)
      expect(normalizeScore(100)).toBe(1.0)
      expect(normalizeScore(85)).toBe(0.85)
    })

    it('should handle edge cases', () => {
      expect(normalizeScore(1)).toBe(1)
      expect(normalizeScore(1.5)).toBe(0.015) // Interpreted as percentage
    })
  })

  describe('toPercentage', () => {
    it('should convert normalized score to percentage string', () => {
      expect(toPercentage(0.5)).toBe('50.0%')
      expect(toPercentage(0.85)).toBe('85.0%')
      expect(toPercentage(1.0)).toBe('100.0%')
    })

    it('should handle percentage input', () => {
      expect(toPercentage(50)).toBe('50.0%')
      expect(toPercentage(85)).toBe('85.0%')
    })

    it('should respect decimal places parameter', () => {
      expect(toPercentage(0.856, 0)).toBe('86%')
      expect(toPercentage(0.856, 1)).toBe('85.6%')
      expect(toPercentage(0.856, 2)).toBe('85.60%')
    })

    it('should handle zero', () => {
      expect(toPercentage(0)).toBe('0.0%')
    })
  })

  describe('getConfidenceColors', () => {
    it('should return high confidence colors', () => {
      const colors = getConfidenceColors('high')
      expect(colors).toEqual(CONFIDENCE_COLORS.high)
      expect(colors.bg).toContain('emerald')
    })

    it('should return medium confidence colors', () => {
      const colors = getConfidenceColors('medium')
      expect(colors).toEqual(CONFIDENCE_COLORS.medium)
      expect(colors.bg).toContain('amber')
    })

    it('should return low confidence colors', () => {
      const colors = getConfidenceColors('low')
      expect(colors).toEqual(CONFIDENCE_COLORS.low)
      expect(colors.bg).toContain('orange')
    })

    it('should return critical confidence colors', () => {
      const colors = getConfidenceColors('critical')
      expect(colors).toEqual(CONFIDENCE_COLORS.critical)
      expect(colors.bg).toContain('red')
    })
  })

  describe('getConfidenceColorsFromScore', () => {
    it('should return correct colors for high scores', () => {
      const colors = getConfidenceColorsFromScore(0.9)
      expect(colors).toEqual(CONFIDENCE_COLORS.high)
    })

    it('should return correct colors for medium scores', () => {
      const colors = getConfidenceColorsFromScore(0.7)
      expect(colors).toEqual(CONFIDENCE_COLORS.medium)
    })

    it('should return correct colors for low scores', () => {
      const colors = getConfidenceColorsFromScore(0.5)
      expect(colors).toEqual(CONFIDENCE_COLORS.low)
    })

    it('should return correct colors for critical scores', () => {
      const colors = getConfidenceColorsFromScore(0.2)
      expect(colors).toEqual(CONFIDENCE_COLORS.critical)
    })

    it('should handle percentage inputs', () => {
      const colors = getConfidenceColorsFromScore(90)
      expect(colors).toEqual(CONFIDENCE_COLORS.high)
    })
  })

  describe('getModelInfo', () => {
    it('should return wildlife_tools info', () => {
      const info = getModelInfo('wildlife_tools')
      expect(info.name).toBe('Wildlife Tools')
      expect(info.weight).toBe(0.40)
    })

    it('should return cvwc2019_reid info', () => {
      const info = getModelInfo('cvwc2019_reid')
      expect(info.name).toBe('CVWC2019')
      expect(info.weight).toBe(0.30)
    })

    it('should return transreid info', () => {
      const info = getModelInfo('transreid')
      expect(info.name).toBe('TransReID')
      expect(info.weight).toBe(0.20)
    })

    it('should return megadescriptor_b info', () => {
      const info = getModelInfo('megadescriptor_b')
      expect(info.name).toBe('MegaDescriptor')
      expect(info.weight).toBe(0.15)
    })

    it('should return tiger_reid info', () => {
      const info = getModelInfo('tiger_reid')
      expect(info.name).toBe('Tiger ReID')
      expect(info.weight).toBe(0.10)
    })

    it('should return rapid_reid info', () => {
      const info = getModelInfo('rapid_reid')
      expect(info.name).toBe('Rapid ReID')
      expect(info.weight).toBe(0.05)
    })

    it('should handle case-insensitive model names', () => {
      const info = getModelInfo('WILDLIFE_TOOLS')
      expect(info.name).toBe('Wildlife Tools')
    })

    it('should handle hyphenated model names', () => {
      const info = getModelInfo('wildlife-tools')
      expect(info.name).toBe('Wildlife Tools')
    })

    it('should return default info for unknown models', () => {
      const info = getModelInfo('unknown_model')
      expect(info.name).toBe('unknown_model')
      expect(info.weight).toBe(0)
      expect(info.bg).toContain('gray')
    })
  })

  describe('getVerificationColors', () => {
    it('should return high_confidence colors', () => {
      const colors = getVerificationColors('high_confidence')
      expect(colors.bg).toContain('emerald')
    })

    it('should return verified colors', () => {
      const colors = getVerificationColors('verified')
      expect(colors.bg).toContain('blue')
    })

    it('should return low_confidence colors', () => {
      const colors = getVerificationColors('low_confidence')
      expect(colors.bg).toContain('amber')
    })

    it('should return error colors', () => {
      const colors = getVerificationColors('error')
      expect(colors.bg).toContain('red')
    })

    it('should return skipped colors as default for unknown status', () => {
      const colors = getVerificationColors('unknown_status' as any)
      expect(colors).toBeDefined()
    })
  })

  describe('MODEL_COLORS', () => {
    it('should have all expected models defined', () => {
      expect(MODEL_COLORS.wildlife_tools).toBeDefined()
      expect(MODEL_COLORS.cvwc2019_reid).toBeDefined()
      expect(MODEL_COLORS.transreid).toBeDefined()
      expect(MODEL_COLORS.megadescriptor_b).toBeDefined()
      expect(MODEL_COLORS.tiger_reid).toBeDefined()
      expect(MODEL_COLORS.rapid_reid).toBeDefined()
    })

    it('should have weights sum approximately to 1.2 (allowing overlap in ensemble)', () => {
      const totalWeight = Object.values(MODEL_COLORS).reduce(
        (sum, model) => sum + model.weight,
        0
      )
      // Weights: 0.40 + 0.30 + 0.20 + 0.15 + 0.10 + 0.05 = 1.20
      expect(totalWeight).toBe(1.20)
    })
  })
})
