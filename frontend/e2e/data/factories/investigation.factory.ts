import { randomUUID } from 'crypto'

export interface InvestigationData {
  investigation_id: string
  status: 'pending' | 'running' | 'completed' | 'error'
  created_at: string
  completed_at: string | null
  image_path: string
  context: {
    location: string
    date: string
    notes: string
  }
  summary?: {
    detection_count: number
    total_matches: number
    confidence: 'high' | 'medium' | 'low'
    top_matches: Array<{
      tiger_id: string
      tiger_name: string
      similarity: number
      model: string
    }>
  }
}

export const investigationFactory = {
  build: (overrides: Partial<InvestigationData> = {}): InvestigationData => ({
    investigation_id: randomUUID(),
    status: 'completed',
    created_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    image_path: '/test-images/tiger.jpg',
    context: {
      location: 'Test Location',
      date: new Date().toISOString().split('T')[0],
      notes: 'Test investigation',
    },
    summary: {
      detection_count: 1,
      total_matches: 5,
      confidence: 'high',
      top_matches: [
        { tiger_id: randomUUID(), tiger_name: 'Tiger A', similarity: 0.95, model: 'wildlife_tools' },
        { tiger_id: randomUUID(), tiger_name: 'Tiger B', similarity: 0.87, model: 'cvwc2019_reid' },
      ],
    },
    ...overrides,
  }),

  buildPending: (overrides: Partial<InvestigationData> = {}): InvestigationData =>
    investigationFactory.build({
      status: 'pending',
      completed_at: null,
      summary: undefined,
      ...overrides,
    }),

  buildRunning: (overrides: Partial<InvestigationData> = {}): InvestigationData =>
    investigationFactory.build({
      status: 'running',
      completed_at: null,
      summary: undefined,
      ...overrides,
    }),

  buildWithError: (overrides: Partial<InvestigationData> = {}): InvestigationData =>
    investigationFactory.build({
      status: 'error',
      completed_at: null,
      summary: undefined,
      ...overrides,
    }),

  buildNoMatches: (overrides: Partial<InvestigationData> = {}): InvestigationData =>
    investigationFactory.build({
      summary: {
        detection_count: 1,
        total_matches: 0,
        confidence: 'low',
        top_matches: [],
      },
      ...overrides,
    }),
}
