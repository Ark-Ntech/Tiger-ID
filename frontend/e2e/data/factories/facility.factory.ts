import { randomUUID } from 'crypto'

export interface FacilityData {
  id: string
  name: string
  url: string
  country: string
  coordinates: { lat: number; lng: number } | null
  tiger_count: number
  discovery_status: 'active' | 'paused' | 'error'
  last_crawled: string | null
  created_at: string
}

export const facilityFactory = {
  build: (overrides: Partial<FacilityData> = {}): FacilityData => ({
    id: randomUUID(),
    name: `Test Facility ${Math.random().toString(36).substring(7)}`,
    url: 'https://example.com/tigers',
    country: 'United States',
    coordinates: { lat: 40.7128, lng: -74.006 },
    tiger_count: Math.floor(Math.random() * 20),
    discovery_status: 'active',
    last_crawled: new Date().toISOString(),
    created_at: new Date().toISOString(),
    ...overrides,
  }),

  buildWithTigers: (tigerCount: number, overrides: Partial<FacilityData> = {}): FacilityData =>
    facilityFactory.build({ tiger_count: tigerCount, ...overrides }),

  buildPaused: (overrides: Partial<FacilityData> = {}): FacilityData =>
    facilityFactory.build({ discovery_status: 'paused', ...overrides }),

  buildWithError: (overrides: Partial<FacilityData> = {}): FacilityData =>
    facilityFactory.build({ discovery_status: 'error', last_crawled: null, ...overrides }),

  buildMany: (count: number, overrides: Partial<FacilityData> = {}): FacilityData[] =>
    Array.from({ length: count }, () => facilityFactory.build(overrides)),
}
