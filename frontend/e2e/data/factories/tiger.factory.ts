import { randomUUID } from 'crypto'

export interface TigerData {
  id: string
  name: string
  confidence_score: number
  facility_id: string
  facility_name: string
  image_path: string
  status: 'verified' | 'pending' | 'unverified'
  created_at: string
  updated_at: string
}

export const tigerFactory = {
  build: (overrides: Partial<TigerData> = {}): TigerData => ({
    id: randomUUID(),
    name: `Tiger-${Math.random().toString(36).substring(7)}`,
    confidence_score: Math.random() * 0.3 + 0.7, // 0.7-1.0
    facility_id: randomUUID(),
    facility_name: 'Test Zoo',
    image_path: '/placeholder-tiger.png',
    status: 'verified',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }),

  buildHighConfidence: (overrides: Partial<TigerData> = {}): TigerData =>
    tigerFactory.build({ confidence_score: 0.95, ...overrides }),

  buildLowConfidence: (overrides: Partial<TigerData> = {}): TigerData =>
    tigerFactory.build({ confidence_score: 0.65, ...overrides }),

  buildPending: (overrides: Partial<TigerData> = {}): TigerData =>
    tigerFactory.build({ status: 'pending', ...overrides }),

  buildMany: (count: number, overrides: Partial<TigerData> = {}): TigerData[] =>
    Array.from({ length: count }, () => tigerFactory.build(overrides)),
}
