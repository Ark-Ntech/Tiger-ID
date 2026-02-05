import { http, HttpResponse, delay } from 'msw'
import { investigationFactory, tigerFactory, type InvestigationData } from '../../data/factories'

const API_BASE = '/api'

// In-memory store for investigations
let investigations: InvestigationData[] = [
  investigationFactory.build(),
  investigationFactory.buildRunning(),
  investigationFactory.buildNoMatches(),
]

// Simulated workflow state
const workflowProgress: Map<string, {
  phase: string
  progress: number
  modelProgress: Record<string, number>
}> = new Map()

export const investigationsHandlers = [
  // Launch investigation (Investigation 2.0)
  http.post(`${API_BASE}/investigation2/launch`, async ({ request }) => {
    await delay(200)

    const formData = await request.formData()
    const image = formData.get('image')

    if (!image) {
      return HttpResponse.json(
        { detail: 'Image is required' },
        { status: 400 }
      )
    }

    const newInvestigation = investigationFactory.buildRunning({
      context: {
        location: formData.get('location') as string || '',
        date: formData.get('date') as string || '',
        notes: formData.get('notes') as string || '',
      },
    })

    investigations.push(newInvestigation)

    // Initialize workflow progress
    workflowProgress.set(newInvestigation.investigation_id, {
      phase: 'upload_and_parse',
      progress: 0,
      modelProgress: {
        wildlife_tools: 0,
        cvwc2019_reid: 0,
        transreid: 0,
        megadescriptor_b: 0,
        tiger_reid: 0,
        rapid_reid: 0,
      },
    })

    return HttpResponse.json({
      success: true,
      investigation_id: newInvestigation.investigation_id,
      status: 'running',
    })
  }),

  // Get investigation status
  http.get(`${API_BASE}/investigation2/:id`, async ({ params }) => {
    await delay(50)

    const { id } = params
    const investigation = investigations.find((i) => i.investigation_id === id)

    if (!investigation) {
      return HttpResponse.json(
        { detail: 'Investigation not found' },
        { status: 404 }
      )
    }

    // Simulate progress if running
    const progress = workflowProgress.get(id as string)
    if (progress && investigation.status === 'running') {
      // Advance progress each poll
      progress.progress += 10
      if (progress.progress >= 100) {
        progress.progress = 0
        // Advance to next phase
        const phases = ['upload_and_parse', 'reverse_image_search', 'tiger_detection', 'stripe_analysis', 'report_generation', 'complete']
        const currentIndex = phases.indexOf(progress.phase)
        if (currentIndex < phases.length - 1) {
          progress.phase = phases[currentIndex + 1]

          // Update model progress during stripe_analysis
          if (progress.phase === 'stripe_analysis') {
            Object.keys(progress.modelProgress).forEach((model) => {
              progress.modelProgress[model] = Math.min(100, progress.modelProgress[model] + Math.random() * 30)
            })
          }
        } else {
          // Complete the investigation
          investigation.status = 'completed'
          investigation.completed_at = new Date().toISOString()
          investigation.summary = {
            detection_count: 1,
            total_matches: 5,
            confidence: 'high',
            top_matches: tigerFactory.buildMany(5).map((t, i) => ({
              tiger_id: t.id,
              tiger_name: t.name,
              similarity: 0.95 - i * 0.05,
              model: ['wildlife_tools', 'cvwc2019_reid', 'transreid'][i % 3],
            })),
          }
        }
      }
    }

    return HttpResponse.json({
      success: true,
      data: investigation,
      progress: progress || null,
    })
  }),

  // List investigations
  http.get(`${API_BASE}/investigation2`, async ({ request }) => {
    await delay(100)

    const url = new URL(request.url)
    const page = parseInt(url.searchParams.get('page') || '1', 10)
    const limit = parseInt(url.searchParams.get('limit') || '20', 10)
    const status = url.searchParams.get('status')

    let filtered = [...investigations]

    if (status) {
      filtered = filtered.filter((i) => i.status === status)
    }

    // Sort by created_at descending
    filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

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

  // Regenerate report
  http.post(`${API_BASE}/investigation2/:id/regenerate-report`, async ({ params, request }) => {
    await delay(500)

    const { id } = params
    const body = await request.json() as { audience: string }
    const investigation = investigations.find((i) => i.investigation_id === id)

    if (!investigation) {
      return HttpResponse.json(
        { detail: 'Investigation not found' },
        { status: 404 }
      )
    }

    if (investigation.status !== 'completed') {
      return HttpResponse.json(
        { detail: 'Investigation must be completed to regenerate report' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      success: true,
      message: `Report regenerated for audience: ${body.audience}`,
    })
  }),

  // Delete investigation
  http.delete(`${API_BASE}/investigation2/:id`, async ({ params }) => {
    await delay(100)

    const { id } = params
    const index = investigations.findIndex((i) => i.investigation_id === id)

    if (index === -1) {
      return HttpResponse.json(
        { detail: 'Investigation not found' },
        { status: 404 }
      )
    }

    investigations.splice(index, 1)
    workflowProgress.delete(id as string)

    return HttpResponse.json({
      success: true,
      message: 'Investigation deleted',
    })
  }),

  // Get investigation report (download)
  http.get(`${API_BASE}/investigation2/:id/report`, async ({ params, request }) => {
    await delay(200)

    const { id } = params
    const url = new URL(request.url)
    const format = url.searchParams.get('format') || 'pdf'
    const investigation = investigations.find((i) => i.investigation_id === id)

    if (!investigation) {
      return HttpResponse.json(
        { detail: 'Investigation not found' },
        { status: 404 }
      )
    }

    // Return mock file response
    return new HttpResponse(
      new Blob(['Mock report content'], { type: format === 'pdf' ? 'application/pdf' : 'application/json' }),
      {
        status: 200,
        headers: {
          'Content-Type': format === 'pdf' ? 'application/pdf' : 'application/json',
          'Content-Disposition': `attachment; filename="investigation-${id}.${format}"`,
        },
      }
    )
  }),
]

// Helper to reset investigations state
export const resetInvestigationsState = (): void => {
  investigations = [
    investigationFactory.build(),
    investigationFactory.buildRunning(),
    investigationFactory.buildNoMatches(),
  ]
  workflowProgress.clear()
}

// Helper to set investigations for tests
export const setInvestigations = (newInvestigations: InvestigationData[]): void => {
  investigations = newInvestigations
}

// Get current investigations (for assertions)
export const getInvestigations = (): InvestigationData[] => [...investigations]
