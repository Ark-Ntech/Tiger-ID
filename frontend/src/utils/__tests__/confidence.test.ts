import { describe, it, expect } from 'vitest'
import {
  CONFIDENCE_THRESHOLDS,
  CONFIDENCE_COLORS,
  MODEL_COLORS,
  VERIFICATION_COLORS,
  getConfidenceLevel,
  normalizeScore,
  toPercentage,
  getConfidenceColors,
  getConfidenceColorsFromScore,
  getModelInfo,
  getVerificationColors,
  type ConfidenceLevel,
  type ModelKey,
  type VerificationStatusKey,
} from '../confidence'

describe('CONFIDENCE_THRESHOLDS', () => {
  it('should have HIGH threshold at 0.85', () => {
    expect(CONFIDENCE_THRESHOLDS.HIGH).toBe(0.85)
  })

  it('should have MEDIUM threshold at 0.65', () => {
    expect(CONFIDENCE_THRESHOLDS.MEDIUM).toBe(0.65)
  })

  it('should have LOW threshold at 0.4', () => {
    expect(CONFIDENCE_THRESHOLDS.LOW).toBe(0.4)
  })
})

describe('getConfidenceLevel', () => {
  describe('normalized scores (0-1)', () => {
    it('should return high for scores >= 0.85', () => {
      expect(getConfidenceLevel(0.85)).toBe('high')
      expect(getConfidenceLevel(0.9)).toBe('high')
      expect(getConfidenceLevel(1.0)).toBe('high')
    })

    it('should return medium for scores >= 0.65 and < 0.85', () => {
      expect(getConfidenceLevel(0.65)).toBe('medium')
      expect(getConfidenceLevel(0.75)).toBe('medium')
      expect(getConfidenceLevel(0.84)).toBe('medium')
    })

    it('should return low for scores >= 0.4 and < 0.65', () => {
      expect(getConfidenceLevel(0.4)).toBe('low')
      expect(getConfidenceLevel(0.5)).toBe('low')
      expect(getConfidenceLevel(0.64)).toBe('low')
    })

    it('should return critical for scores < 0.4', () => {
      expect(getConfidenceLevel(0.39)).toBe('critical')
      expect(getConfidenceLevel(0.2)).toBe('critical')
      expect(getConfidenceLevel(0)).toBe('critical')
    })
  })

  describe('percentage scores (0-100)', () => {
    it('should normalize and return high for scores >= 85', () => {
      expect(getConfidenceLevel(85)).toBe('high')
      expect(getConfidenceLevel(90)).toBe('high')
      expect(getConfidenceLevel(100)).toBe('high')
    })

    it('should normalize and return medium for scores >= 65 and < 85', () => {
      expect(getConfidenceLevel(65)).toBe('medium')
      expect(getConfidenceLevel(75)).toBe('medium')
      expect(getConfidenceLevel(84)).toBe('medium')
    })

    it('should normalize and return low for scores >= 40 and < 65', () => {
      expect(getConfidenceLevel(40)).toBe('low')
      expect(getConfidenceLevel(50)).toBe('low')
      expect(getConfidenceLevel(64)).toBe('low')
    })

    it('should normalize and return critical for scores < 40', () => {
      expect(getConfidenceLevel(39)).toBe('critical')
      expect(getConfidenceLevel(20)).toBe('critical')
      expect(getConfidenceLevel(0)).toBe('critical')
    })
  })

  describe('edge cases', () => {
    it('should handle exact threshold values', () => {
      expect(getConfidenceLevel(0.85)).toBe('high')
      expect(getConfidenceLevel(0.65)).toBe('medium')
      expect(getConfidenceLevel(0.4)).toBe('low')
    })

    it('should handle values just below thresholds', () => {
      expect(getConfidenceLevel(0.8499)).toBe('medium')
      expect(getConfidenceLevel(0.6499)).toBe('low')
      expect(getConfidenceLevel(0.3999)).toBe('critical')
    })
  })
})

describe('normalizeScore', () => {
  it('should return same value for scores <= 1', () => {
    expect(normalizeScore(0.5)).toBe(0.5)
    expect(normalizeScore(0)).toBe(0)
    expect(normalizeScore(1)).toBe(1)
    expect(normalizeScore(0.75)).toBe(0.75)
  })

  it('should normalize scores > 1 by dividing by 100', () => {
    expect(normalizeScore(50)).toBe(0.5)
    expect(normalizeScore(100)).toBe(1)
    expect(normalizeScore(75)).toBe(0.75)
    expect(normalizeScore(25)).toBe(0.25)
  })

  it('should handle edge cases', () => {
    expect(normalizeScore(1.0)).toBe(1)
    expect(normalizeScore(1.01)).toBe(0.0101)
  })
})

describe('toPercentage', () => {
  describe('with default decimals', () => {
    it('should convert normalized scores to percentage strings', () => {
      expect(toPercentage(0.5)).toBe('50.0%')
      expect(toPercentage(1)).toBe('100.0%')
      expect(toPercentage(0)).toBe('0.0%')
      expect(toPercentage(0.333)).toBe('33.3%')
    })

    it('should normalize percentage scores first', () => {
      expect(toPercentage(50)).toBe('50.0%')
      expect(toPercentage(100)).toBe('100.0%')
      expect(toPercentage(75)).toBe('75.0%')
    })
  })

  describe('with custom decimals', () => {
    it('should format with 0 decimals', () => {
      expect(toPercentage(0.555, 0)).toBe('56%')
      expect(toPercentage(0.5, 0)).toBe('50%')
    })

    it('should format with 2 decimals', () => {
      expect(toPercentage(0.5555, 2)).toBe('55.55%')
      expect(toPercentage(0.3333, 2)).toBe('33.33%')
    })

    it('should format with 3 decimals', () => {
      expect(toPercentage(0.55555, 3)).toBe('55.555%')
    })
  })
})

describe('CONFIDENCE_COLORS', () => {
  describe('high confidence colors', () => {
    it('should have emerald-based colors', () => {
      expect(CONFIDENCE_COLORS.high.bg).toContain('emerald')
      expect(CONFIDENCE_COLORS.high.bgSolid).toContain('emerald')
      expect(CONFIDENCE_COLORS.high.text).toContain('emerald')
      expect(CONFIDENCE_COLORS.high.border).toContain('emerald')
    })
  })

  describe('medium confidence colors', () => {
    it('should have amber-based colors', () => {
      expect(CONFIDENCE_COLORS.medium.bg).toContain('amber')
      expect(CONFIDENCE_COLORS.medium.bgSolid).toContain('amber')
      expect(CONFIDENCE_COLORS.medium.text).toContain('amber')
      expect(CONFIDENCE_COLORS.medium.border).toContain('amber')
    })
  })

  describe('low confidence colors', () => {
    it('should have orange-based colors', () => {
      expect(CONFIDENCE_COLORS.low.bg).toContain('orange')
      expect(CONFIDENCE_COLORS.low.bgSolid).toContain('orange')
      expect(CONFIDENCE_COLORS.low.text).toContain('orange')
      expect(CONFIDENCE_COLORS.low.border).toContain('orange')
    })
  })

  describe('critical confidence colors', () => {
    it('should have red-based colors', () => {
      expect(CONFIDENCE_COLORS.critical.bg).toContain('red')
      expect(CONFIDENCE_COLORS.critical.bgSolid).toContain('red')
      expect(CONFIDENCE_COLORS.critical.text).toContain('red')
      expect(CONFIDENCE_COLORS.critical.border).toContain('red')
    })
  })
})

describe('getConfidenceColors', () => {
  it('should return high colors for high level', () => {
    expect(getConfidenceColors('high')).toEqual(CONFIDENCE_COLORS.high)
  })

  it('should return medium colors for medium level', () => {
    expect(getConfidenceColors('medium')).toEqual(CONFIDENCE_COLORS.medium)
  })

  it('should return low colors for low level', () => {
    expect(getConfidenceColors('low')).toEqual(CONFIDENCE_COLORS.low)
  })

  it('should return critical colors for critical level', () => {
    expect(getConfidenceColors('critical')).toEqual(CONFIDENCE_COLORS.critical)
  })
})

describe('getConfidenceColorsFromScore', () => {
  it('should return high colors for high scores', () => {
    expect(getConfidenceColorsFromScore(0.9)).toEqual(CONFIDENCE_COLORS.high)
  })

  it('should return medium colors for medium scores', () => {
    expect(getConfidenceColorsFromScore(0.7)).toEqual(CONFIDENCE_COLORS.medium)
  })

  it('should return low colors for low scores', () => {
    expect(getConfidenceColorsFromScore(0.5)).toEqual(CONFIDENCE_COLORS.low)
  })

  it('should return critical colors for critical scores', () => {
    expect(getConfidenceColorsFromScore(0.2)).toEqual(CONFIDENCE_COLORS.critical)
  })

  it('should handle percentage scores', () => {
    expect(getConfidenceColorsFromScore(90)).toEqual(CONFIDENCE_COLORS.high)
    expect(getConfidenceColorsFromScore(70)).toEqual(CONFIDENCE_COLORS.medium)
  })
})

describe('MODEL_COLORS', () => {
  it('should have wildlife_tools model', () => {
    expect(MODEL_COLORS.wildlife_tools).toBeDefined()
    expect(MODEL_COLORS.wildlife_tools.name).toBe('Wildlife Tools')
    expect(MODEL_COLORS.wildlife_tools.weight).toBe(0.4)
  })

  it('should have cvwc2019_reid model', () => {
    expect(MODEL_COLORS.cvwc2019_reid).toBeDefined()
    expect(MODEL_COLORS.cvwc2019_reid.name).toBe('CVWC2019')
    expect(MODEL_COLORS.cvwc2019_reid.weight).toBe(0.3)
  })

  it('should have transreid model', () => {
    expect(MODEL_COLORS.transreid).toBeDefined()
    expect(MODEL_COLORS.transreid.name).toBe('TransReID')
    expect(MODEL_COLORS.transreid.weight).toBe(0.2)
  })

  it('should have megadescriptor_b model', () => {
    expect(MODEL_COLORS.megadescriptor_b).toBeDefined()
    expect(MODEL_COLORS.megadescriptor_b.name).toBe('MegaDescriptor')
    expect(MODEL_COLORS.megadescriptor_b.weight).toBe(0.15)
  })

  it('should have tiger_reid model', () => {
    expect(MODEL_COLORS.tiger_reid).toBeDefined()
    expect(MODEL_COLORS.tiger_reid.name).toBe('Tiger ReID')
    expect(MODEL_COLORS.tiger_reid.weight).toBe(0.1)
  })

  it('should have rapid_reid model', () => {
    expect(MODEL_COLORS.rapid_reid).toBeDefined()
    expect(MODEL_COLORS.rapid_reid.name).toBe('Rapid ReID')
    expect(MODEL_COLORS.rapid_reid.weight).toBe(0.05)
  })

  it('model weights should sum to 1.2 (ensemble with overlap)', () => {
    const totalWeight = Object.values(MODEL_COLORS).reduce(
      (sum, model) => sum + model.weight,
      0
    )
    expect(totalWeight).toBeCloseTo(1.2, 2)
  })
})

describe('getModelInfo', () => {
  it('should return model info for exact key', () => {
    const info = getModelInfo('wildlife_tools')
    expect(info.name).toBe('Wildlife Tools')
    expect(info.weight).toBe(0.4)
  })

  it('should normalize model key with spaces', () => {
    const info = getModelInfo('wildlife tools')
    expect(info.name).toBe('Wildlife Tools')
  })

  it('should normalize model key with hyphens', () => {
    const info = getModelInfo('wildlife-tools')
    expect(info.name).toBe('Wildlife Tools')
  })

  it('should handle uppercase model keys', () => {
    const info = getModelInfo('WILDLIFE_TOOLS')
    expect(info.name).toBe('Wildlife Tools')
  })

  it('should return default for unknown model', () => {
    const info = getModelInfo('unknown_model')
    expect(info.name).toBe('unknown_model')
    expect(info.weight).toBe(0)
    expect(info.bg).toBe('bg-gray-500')
  })
})

describe('VERIFICATION_COLORS', () => {
  it('should have high_confidence status', () => {
    expect(VERIFICATION_COLORS.high_confidence).toBeDefined()
    expect(VERIFICATION_COLORS.high_confidence.bg).toContain('emerald')
  })

  it('should have verified status', () => {
    expect(VERIFICATION_COLORS.verified).toBeDefined()
    expect(VERIFICATION_COLORS.verified.bg).toContain('blue')
  })

  it('should have low_confidence status', () => {
    expect(VERIFICATION_COLORS.low_confidence).toBeDefined()
    expect(VERIFICATION_COLORS.low_confidence.bg).toContain('amber')
  })

  it('should have insufficient_matches status', () => {
    expect(VERIFICATION_COLORS.insufficient_matches).toBeDefined()
    expect(VERIFICATION_COLORS.insufficient_matches.bg).toContain('gray')
  })

  it('should have skipped status', () => {
    expect(VERIFICATION_COLORS.skipped).toBeDefined()
    expect(VERIFICATION_COLORS.skipped.bg).toContain('gray')
  })

  it('should have error status', () => {
    expect(VERIFICATION_COLORS.error).toBeDefined()
    expect(VERIFICATION_COLORS.error.bg).toContain('red')
  })
})

describe('getVerificationColors', () => {
  it('should return colors for high_confidence', () => {
    expect(getVerificationColors('high_confidence')).toEqual(
      VERIFICATION_COLORS.high_confidence
    )
  })

  it('should return colors for verified', () => {
    expect(getVerificationColors('verified')).toEqual(VERIFICATION_COLORS.verified)
  })

  it('should return colors for low_confidence', () => {
    expect(getVerificationColors('low_confidence')).toEqual(
      VERIFICATION_COLORS.low_confidence
    )
  })

  it('should return colors for insufficient_matches', () => {
    expect(getVerificationColors('insufficient_matches')).toEqual(
      VERIFICATION_COLORS.insufficient_matches
    )
  })

  it('should return colors for skipped', () => {
    expect(getVerificationColors('skipped')).toEqual(VERIFICATION_COLORS.skipped)
  })

  it('should return colors for error', () => {
    expect(getVerificationColors('error')).toEqual(VERIFICATION_COLORS.error)
  })

  it('should return skipped colors for unknown status', () => {
    const unknownStatus = 'unknown_status' as VerificationStatusKey
    expect(getVerificationColors(unknownStatus)).toEqual(VERIFICATION_COLORS.skipped)
  })
})
