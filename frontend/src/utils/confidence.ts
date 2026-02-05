/**
 * Standardized confidence scoring utilities for Tiger ID
 * Used across match cards, methodology, and results components
 */

// Confidence thresholds for categorization
export const CONFIDENCE_THRESHOLDS = {
  HIGH: 0.85,
  MEDIUM: 0.65,
  LOW: 0.4,
} as const

export type ConfidenceLevel = 'high' | 'medium' | 'low' | 'critical'

/**
 * Determine confidence level from a score (0-1 or 0-100)
 * Automatically normalizes scores > 1 to 0-1 range
 */
export function getConfidenceLevel(score: number): ConfidenceLevel {
  // Normalize if score is in 0-100 range
  const normalizedScore = score > 1 ? score / 100 : score

  if (normalizedScore >= CONFIDENCE_THRESHOLDS.HIGH) return 'high'
  if (normalizedScore >= CONFIDENCE_THRESHOLDS.MEDIUM) return 'medium'
  if (normalizedScore >= CONFIDENCE_THRESHOLDS.LOW) return 'low'
  return 'critical'
}

/**
 * Get normalized score (0-1 range)
 */
export function normalizeScore(score: number): number {
  return score > 1 ? score / 100 : score
}

/**
 * Get percentage from normalized score
 */
export function toPercentage(score: number, decimals = 1): string {
  const normalized = normalizeScore(score)
  return `${(normalized * 100).toFixed(decimals)}%`
}

// Tactical Intelligence color palette for confidence levels
export const CONFIDENCE_COLORS = {
  high: {
    bg: 'bg-emerald-100 dark:bg-emerald-900/30',
    bgSolid: 'bg-emerald-500 dark:bg-emerald-600',
    text: 'text-emerald-700 dark:text-emerald-400',
    border: 'border-emerald-300 dark:border-emerald-700',
    ring: 'ring-emerald-500/20',
    gradient: 'from-emerald-500 to-emerald-600',
  },
  medium: {
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    bgSolid: 'bg-amber-500 dark:bg-amber-600',
    text: 'text-amber-700 dark:text-amber-400',
    border: 'border-amber-300 dark:border-amber-700',
    ring: 'ring-amber-500/20',
    gradient: 'from-amber-500 to-amber-600',
  },
  low: {
    bg: 'bg-orange-100 dark:bg-orange-900/30',
    bgSolid: 'bg-orange-500 dark:bg-orange-600',
    text: 'text-orange-700 dark:text-orange-400',
    border: 'border-orange-300 dark:border-orange-700',
    ring: 'ring-orange-500/20',
    gradient: 'from-orange-500 to-orange-600',
  },
  critical: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    bgSolid: 'bg-red-500 dark:bg-red-600',
    text: 'text-red-700 dark:text-red-400',
    border: 'border-red-300 dark:border-red-700',
    ring: 'ring-red-500/20',
    gradient: 'from-red-500 to-red-600',
  },
} as const

/**
 * Get all color classes for a confidence level
 */
export function getConfidenceColors(level: ConfidenceLevel) {
  return CONFIDENCE_COLORS[level]
}

/**
 * Get confidence colors from a score
 */
export function getConfidenceColorsFromScore(score: number) {
  return CONFIDENCE_COLORS[getConfidenceLevel(score)]
}

// Model-specific colors for ensemble visualization
export const MODEL_COLORS = {
  wildlife_tools: {
    bg: 'bg-blue-600',
    bgLight: 'bg-blue-100 dark:bg-blue-900/30',
    text: 'text-blue-700 dark:text-blue-400',
    name: 'Wildlife Tools',
    weight: 0.40,
  },
  cvwc2019_reid: {
    bg: 'bg-green-600',
    bgLight: 'bg-green-100 dark:bg-green-900/30',
    text: 'text-green-700 dark:text-green-400',
    name: 'CVWC2019',
    weight: 0.30,
  },
  transreid: {
    bg: 'bg-purple-600',
    bgLight: 'bg-purple-100 dark:bg-purple-900/30',
    text: 'text-purple-700 dark:text-purple-400',
    name: 'TransReID',
    weight: 0.20,
  },
  megadescriptor_b: {
    bg: 'bg-teal-600',
    bgLight: 'bg-teal-100 dark:bg-teal-900/30',
    text: 'text-teal-700 dark:text-teal-400',
    name: 'MegaDescriptor',
    weight: 0.15,
  },
  tiger_reid: {
    bg: 'bg-tiger-orange',
    bgLight: 'bg-orange-100 dark:bg-orange-900/30',
    text: 'text-orange-700 dark:text-orange-400',
    name: 'Tiger ReID',
    weight: 0.10,
  },
  rapid_reid: {
    bg: 'bg-slate-500',
    bgLight: 'bg-slate-100 dark:bg-slate-900/30',
    text: 'text-slate-700 dark:text-slate-400',
    name: 'Rapid ReID',
    weight: 0.05,
  },
} as const

export type ModelKey = keyof typeof MODEL_COLORS

/**
 * Get model display info
 */
export function getModelInfo(modelKey: string) {
  const key = modelKey.toLowerCase().replace(/[\s-]/g, '_') as ModelKey
  return MODEL_COLORS[key] || {
    bg: 'bg-gray-500',
    bgLight: 'bg-gray-100 dark:bg-gray-800',
    text: 'text-gray-700 dark:text-gray-400',
    name: modelKey,
    weight: 0,
  }
}

// Verification status colors
export const VERIFICATION_COLORS = {
  high_confidence: {
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    text: 'text-emerald-700 dark:text-emerald-400',
    border: 'border-emerald-200 dark:border-emerald-800',
    badge: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300',
  },
  verified: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    text: 'text-blue-700 dark:text-blue-400',
    border: 'border-blue-200 dark:border-blue-800',
    badge: 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300',
  },
  low_confidence: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    text: 'text-amber-700 dark:text-amber-400',
    border: 'border-amber-200 dark:border-amber-800',
    badge: 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300',
  },
  insufficient_matches: {
    bg: 'bg-gray-50 dark:bg-gray-800/50',
    text: 'text-gray-600 dark:text-gray-400',
    border: 'border-gray-200 dark:border-gray-700',
    badge: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
  },
  skipped: {
    bg: 'bg-gray-50 dark:bg-gray-800/50',
    text: 'text-gray-500 dark:text-gray-500',
    border: 'border-gray-200 dark:border-gray-700',
    badge: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-500',
  },
  error: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    text: 'text-red-700 dark:text-red-400',
    border: 'border-red-200 dark:border-red-800',
    badge: 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300',
  },
} as const

export type VerificationStatusKey = keyof typeof VERIFICATION_COLORS

export function getVerificationColors(status: VerificationStatusKey) {
  return VERIFICATION_COLORS[status] || VERIFICATION_COLORS.skipped
}
