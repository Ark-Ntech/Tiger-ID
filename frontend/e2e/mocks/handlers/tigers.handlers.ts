import { http, HttpResponse, delay } from 'msw'
import { tigerFactory, type TigerData } from '../../data/factories'

const API_BASE = '/api'

// In-memory store for tigers
let tigers: TigerData[] = tigerFactory.buildMany(10)

export const tigersHandlers = [
  // List tigers
  http.get(`${API_BASE}/tigers`, async ({ request }) => {
    await delay(100)

    const url = new URL(request.url)
    const page = parseInt(url.searchParams.get('page') || '1', 10)
    const limit = parseInt(url.searchParams.get('limit') || '20', 10)
    const search = url.searchParams.get('search') || ''
    const facilityId = url.searchParams.get('facility_id')
    const status = url.searchParams.get('status')
    const minConfidence = url.searchParams.get('min_confidence')

    let filtered = [...tigers]

    // Apply filters
    if (search) {
      filtered = filtered.filter(
        (t) =>
          t.name.toLowerCase().includes(search.toLowerCase()) ||
          t.facility_name.toLowerCase().includes(search.toLowerCase())
      )
    }

    if (facilityId) {
      filtered = filtered.filter((t) => t.facility_id === facilityId)
    }

    if (status) {
      filtered = filtered.filter((t) => t.status === status)
    }

    if (minConfidence) {
      const minConf = parseFloat(minConfidence)
      filtered = filtered.filter((t) => t.confidence_score >= minConf)
    }

    // Paginate
    const start = (page - 1) * limit
    const end = start + limit
    const paginated = filtered.slice(start, end)

    return HttpResponse.json({
      success: true,
      data: paginated,
      pagination: {
        page,
        limit,
        total: filtered.length,
        total_pages: Math.ceil(filtered.length / limit),
      },
    })
  }),

  // Get single tiger
  http.get(`${API_BASE}/tigers/:id`, async ({ params }) => {
    await delay(50)

    const { id } = params
    const tiger = tigers.find((t) => t.id === id)

    if (!tiger) {
      return HttpResponse.json(
        { detail: 'Tiger not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: tiger,
    })
  }),

  // Create tiger (register)
  http.post(`${API_BASE}/tigers`, async ({ request }) => {
    await delay(150)

    const body = await request.json() as Partial<TigerData>

    if (!body.name) {
      return HttpResponse.json(
        { detail: 'Name is required' },
        { status: 400 }
      )
    }

    const newTiger = tigerFactory.build({
      name: body.name,
      facility_id: body.facility_id,
      facility_name: body.facility_name,
      status: 'pending',
      confidence_score: 0,
    })

    tigers.push(newTiger)

    return HttpResponse.json({
      success: true,
      data: newTiger,
    })
  }),

  // Update tiger
  http.patch(`${API_BASE}/tigers/:id`, async ({ params, request }) => {
    await delay(100)

    const { id } = params
    const body = await request.json() as Partial<TigerData>
    const index = tigers.findIndex((t) => t.id === id)

    if (index === -1) {
      return HttpResponse.json(
        { detail: 'Tiger not found' },
        { status: 404 }
      )
    }

    tigers[index] = {
      ...tigers[index],
      ...body,
      updated_at: new Date().toISOString(),
    }

    return HttpResponse.json({
      success: true,
      data: tigers[index],
    })
  }),

  // Delete tiger
  http.delete(`${API_BASE}/tigers/:id`, async ({ params }) => {
    await delay(100)

    const { id } = params
    const index = tigers.findIndex((t) => t.id === id)

    if (index === -1) {
      return HttpResponse.json(
        { detail: 'Tiger not found' },
        { status: 404 }
      )
    }

    tigers.splice(index, 1)

    return HttpResponse.json({
      success: true,
      message: 'Tiger deleted',
    })
  }),

  // Identify tiger (batch identification)
  http.post(`${API_BASE}/tigers/identify`, async ({ request }) => {
    await delay(500) // Simulate ML processing time

    const formData = await request.formData()
    const image = formData.get('image')

    if (!image) {
      return HttpResponse.json(
        { detail: 'Image is required' },
        { status: 400 }
      )
    }

    // Return mock identification results
    const matches = tigers
      .slice(0, 5)
      .map((tiger, index) => ({
        tiger_id: tiger.id,
        tiger_name: tiger.name,
        similarity: 0.95 - index * 0.05,
        model: ['wildlife_tools', 'cvwc2019_reid', 'transreid'][index % 3],
      }))

    return HttpResponse.json({
      success: true,
      data: {
        detection_count: 1,
        matches,
      },
    })
  }),

  // Compare tigers
  http.post(`${API_BASE}/tigers/compare`, async ({ request }) => {
    await delay(300)

    const body = await request.json() as { tiger_ids: string[] }

    if (!body.tiger_ids || body.tiger_ids.length < 2) {
      return HttpResponse.json(
        { detail: 'At least 2 tiger IDs are required' },
        { status: 400 }
      )
    }

    const selectedTigers = tigers.filter((t) => body.tiger_ids.includes(t.id))

    // Generate mock comparison results
    const comparisons = []
    for (let i = 0; i < selectedTigers.length; i++) {
      for (let j = i + 1; j < selectedTigers.length; j++) {
        comparisons.push({
          tiger_a: selectedTigers[i].id,
          tiger_b: selectedTigers[j].id,
          similarity: Math.random() * 0.3 + 0.5, // 0.5-0.8
          is_same: Math.random() > 0.5,
        })
      }
    }

    return HttpResponse.json({
      success: true,
      data: {
        tigers: selectedTigers,
        comparisons,
      },
    })
  }),
]

// Helper to reset tigers state
export const resetTigersState = (): void => {
  tigers = tigerFactory.buildMany(10)
}

// Helper to set tigers for tests
export const setTigers = (newTigers: TigerData[]): void => {
  tigers = newTigers
}

// Get current tigers (for assertions)
export const getTigers = (): TigerData[] => [...tigers]
