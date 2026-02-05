/**
 * Factory for creating verification queue test data
 */

export interface VerificationItemFactory {
  id: string
  query_image_url: string
  match_image_url: string
  query_tiger_id: string | null
  match_tiger_id: string
  confidence: number
  status: 'pending' | 'approved' | 'rejected'
  entity_type: 'tiger' | 'facility'
  model_scores: {
    wildlife_tools: number
    cvwc2019_reid: number
    transreid: number
    megadescriptor_b: number
    tiger_reid: number
    rapid_reid: number
  }
  model_agreement: number
  created_at: string
  reviewed_at: string | null
  reviewed_by: string | null
  facility_name?: string
  notes?: string
}

export function createVerificationItem(
  overrides: Partial<VerificationItemFactory> = {}
): VerificationItemFactory {
  const baseItem: VerificationItemFactory = {
    id: `verify-${Math.random().toString(36).substr(2, 9)}`,
    query_image_url: '/images/tigers/query-1.jpg',
    match_image_url: '/images/tigers/match-1.jpg',
    query_tiger_id: null,
    match_tiger_id: `tiger-${Math.random().toString(36).substr(2, 9)}`,
    confidence: 0.85,
    status: 'pending',
    entity_type: 'tiger',
    model_scores: {
      wildlife_tools: 0.88,
      cvwc2019_reid: 0.86,
      transreid: 0.84,
      megadescriptor_b: 0.82,
      tiger_reid: 0.81,
      rapid_reid: 0.79,
    },
    model_agreement: 0.83,
    created_at: new Date().toISOString(),
    reviewed_at: null,
    reviewed_by: null,
    ...overrides,
  }

  return baseItem
}

export function createHighConfidenceItem(
  overrides: Partial<VerificationItemFactory> = {}
): VerificationItemFactory {
  return createVerificationItem({
    confidence: 0.95,
    model_scores: {
      wildlife_tools: 0.96,
      cvwc2019_reid: 0.95,
      transreid: 0.94,
      megadescriptor_b: 0.93,
      tiger_reid: 0.92,
      rapid_reid: 0.91,
    },
    model_agreement: 0.94,
    ...overrides,
  })
}

export function createLowConfidenceItem(
  overrides: Partial<VerificationItemFactory> = {}
): VerificationItemFactory {
  return createVerificationItem({
    confidence: 0.65,
    model_scores: {
      wildlife_tools: 0.68,
      cvwc2019_reid: 0.66,
      transreid: 0.64,
      megadescriptor_b: 0.63,
      tiger_reid: 0.62,
      rapid_reid: 0.60,
    },
    model_agreement: 0.64,
    ...overrides,
  })
}

export function createApprovedItem(
  overrides: Partial<VerificationItemFactory> = {}
): VerificationItemFactory {
  return createVerificationItem({
    status: 'approved',
    reviewed_at: new Date().toISOString(),
    reviewed_by: 'testuser',
    ...overrides,
  })
}

export function createRejectedItem(
  overrides: Partial<VerificationItemFactory> = {}
): VerificationItemFactory {
  return createVerificationItem({
    status: 'rejected',
    reviewed_at: new Date().toISOString(),
    reviewed_by: 'testuser',
    notes: 'False positive - different stripe pattern',
    ...overrides,
  })
}

export function createFacilityVerificationItem(
  overrides: Partial<VerificationItemFactory> = {}
): VerificationItemFactory {
  return createVerificationItem({
    entity_type: 'facility',
    facility_name: 'Test Wildlife Sanctuary',
    confidence: 0.78,
    ...overrides,
  })
}

export function createVerificationQueue(count: number): VerificationItemFactory[] {
  const items: VerificationItemFactory[] = []

  for (let i = 0; i < count; i++) {
    if (i % 5 === 0) {
      items.push(createHighConfidenceItem())
    } else if (i % 5 === 1) {
      items.push(createLowConfidenceItem())
    } else if (i % 5 === 2) {
      items.push(createFacilityVerificationItem())
    } else if (i % 5 === 3) {
      items.push(createApprovedItem())
    } else {
      items.push(createVerificationItem())
    }
  }

  return items
}
