import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card'
import Badge from '../components/common/Badge'
import Button from '../components/common/Button'
import {
  BookOpenIcon,
  RocketLaunchIcon,
  MagnifyingGlassCircleIcon,
  IdentificationIcon,
  BuildingOfficeIcon,
  CpuChipIcon,
  ServerStackIcon,
  SparklesIcon,
  CommandLineIcon,
  ChevronRightIcon,
  ArrowUpIcon,
} from '@heroicons/react/24/outline'

// Table of contents sections
const tocSections = [
  { id: 'getting-started', label: 'Getting Started', icon: RocketLaunchIcon },
  { id: 'investigation-workflow', label: 'Investigation Workflow', icon: MagnifyingGlassCircleIcon },
  { id: 'tiger-database', label: 'Tiger Database', icon: IdentificationIcon },
  { id: 'facilities', label: 'Facilities', icon: BuildingOfficeIcon },
  { id: 'ml-ensemble', label: 'ML Ensemble', icon: CpuChipIcon },
  { id: 'mcp-servers', label: 'MCP Servers', icon: ServerStackIcon },
  { id: 'skills', label: 'Skills', icon: SparklesIcon },
  { id: 'api-reference', label: 'API Reference', icon: CommandLineIcon },
]

// Investigation workflow phases
const workflowPhases = [
  {
    phase: 1,
    name: 'Upload & Parse',
    key: 'upload_and_parse',
    description: 'Image validation, EXIF metadata extraction, and initial quality assessment. The system checks resolution, blur level, and stripe visibility to ensure the image is suitable for identification.',
    details: ['Supported formats: JPEG, PNG, WebP', 'EXIF data extraction (GPS, camera, timestamp)', 'Image quality scoring via OpenCV', 'Automatic orientation correction'],
  },
  {
    phase: 2,
    name: 'Reverse Image Search',
    key: 'reverse_image_search',
    description: 'Web intelligence gathering using reverse image search and deep research tools. Searches for matching images across the internet to find potential source facilities or trafficking networks.',
    details: ['DuckDuckGo reverse image search', 'Firecrawl web scraping', 'YouTube data extraction', 'Meta/Facebook data analysis'],
  },
  {
    phase: 3,
    name: 'Tiger Detection',
    key: 'tiger_detection',
    description: 'MegaDetector v5 processes the image to detect and localize tigers using bounding boxes. Non-tiger regions are cropped out to improve re-identification accuracy.',
    details: ['MegaDetector v5 object detection', 'Bounding box extraction', 'Multi-tiger detection support', 'Confidence thresholding'],
  },
  {
    phase: 4,
    name: 'Stripe Analysis',
    key: 'stripe_analysis',
    description: 'The core re-identification step. Six parallel ML models analyze the unique stripe patterns of detected tigers, generating embeddings that are compared against the known gallery.',
    details: ['6-model parallel ensemble', 'Embedding similarity search via sqlite-vec', 'Weighted confidence scoring', 'Cross-model agreement verification'],
  },
  {
    phase: 5,
    name: 'Report Generation',
    key: 'report_generation',
    description: 'Claude AI synthesizes all findings from previous phases into a comprehensive investigation report. Reports are tailored to the target audience.',
    details: ['Law enforcement reports', 'Conservation organization reports', 'Internal analysis reports', 'Public-facing summaries'],
  },
  {
    phase: 6,
    name: 'Complete',
    key: 'complete',
    description: 'Results finalization. All matches, evidence, and generated reports are stored and made available for review, verification, and download.',
    details: ['Match results with confidence scores', 'Evidence chain documentation', 'PDF report download', 'Verification queue integration'],
  },
]

// ML ensemble models
const ensembleModels = [
  {
    name: 'wildlife_tools',
    weight: 0.40,
    embeddingDim: 1536,
    calibrationTemp: 1.0,
    description: 'Primary wildlife re-identification model with the highest weight. Trained on diverse wildlife datasets with strong generalization capabilities.',
  },
  {
    name: 'cvwc2019_reid',
    weight: 0.30,
    embeddingDim: 2048,
    calibrationTemp: 0.85,
    description: 'Computer Vision for Wildlife Conservation 2019 re-identification model. Specialized for tiger identification with high-dimensional embeddings.',
  },
  {
    name: 'transreid',
    weight: 0.20,
    embeddingDim: 768,
    calibrationTemp: 1.1,
    description: 'Transformer-based re-identification model. Uses attention mechanisms for fine-grained stripe pattern recognition.',
  },
  {
    name: 'megadescriptor_b',
    weight: 0.15,
    embeddingDim: 1024,
    calibrationTemp: 1.0,
    description: 'MegaDescriptor base model. Provides complementary feature representations for ensemble diversity.',
  },
  {
    name: 'tiger_reid',
    weight: 0.10,
    embeddingDim: 2048,
    calibrationTemp: 0.9,
    description: 'Tiger-specific re-identification model fine-tuned exclusively on tiger stripe pattern data.',
  },
  {
    name: 'rapid_reid',
    weight: 0.05,
    embeddingDim: 2048,
    calibrationTemp: 0.95,
    description: 'Lightweight rapid re-identification model optimized for speed. Used as a tiebreaker in ensemble voting.',
  },
]

// Ensemble modes
const ensembleModes = [
  {
    name: 'Staggered',
    key: 'staggered',
    description: 'Models execute in weight order. If a high-confidence match is found early, subsequent models are skipped. Optimizes for speed when matches are clear-cut.',
    best: 'Quick lookups with high-confidence matches',
  },
  {
    name: 'Parallel',
    key: 'parallel',
    description: 'All models execute simultaneously and vote on the best match. Each model gets one vote weighted by its ensemble weight.',
    best: 'Balanced speed and accuracy',
  },
  {
    name: 'Weighted',
    key: 'weighted',
    description: 'All models execute and their similarity scores are combined using a weighted average. The recommended mode for most investigations.',
    best: 'Standard investigations (recommended)',
  },
  {
    name: 'Verified',
    key: 'verified',
    description: 'All models must agree above a threshold for a match to be confirmed. Produces the highest confidence results but may miss marginal matches.',
    best: 'Legal evidence and high-stakes identifications',
  },
]

// MCP servers
const mcpServers = {
  core: [
    { name: 'sequential_thinking_server', description: 'Reasoning chain tracking for investigation logic', purpose: 'Maintains step-by-step reasoning traces during investigation workflows' },
    { name: 'image_analysis_server', description: 'Quality assessment via OpenCV', purpose: 'Blur detection, resolution checking, stripe visibility scoring' },
    { name: 'deep_research_server', description: 'DuckDuckGo web research', purpose: 'Internet-scale search for tiger images and facility information' },
    { name: 'report_generation_server', description: 'Multi-audience report generation', purpose: 'Law enforcement, conservation, internal, and public reports' },
  ],
  integration: [
    { name: 'database_server', description: 'Database operations', purpose: 'SQLite + sqlite-vec CRUD and vector similarity queries' },
    { name: 'firecrawl_server', description: 'Web scraping via Firecrawl', purpose: 'Structured data extraction from facility websites' },
    { name: 'tiger_id_server', description: 'Tiger identification operations', purpose: 'Embedding generation, gallery search, match ranking' },
    { name: 'youtube_server', description: 'YouTube data extraction', purpose: 'Video metadata and thumbnail analysis for tiger content' },
    { name: 'meta_server', description: 'Meta/Facebook data', purpose: 'Social media intelligence gathering' },
  ],
  browser: [
    { name: 'puppeteer_server', description: 'Playwright browser automation', purpose: 'JavaScript-rendered page crawling and interaction' },
    { name: 'puppeteer_mcp_standalone', description: 'Standalone Puppeteer MCP', purpose: 'Independent browser automation for parallel crawling' },
  ],
}

// Skills
const skills = [
  { name: '/synthesize-evidence', description: 'Weighted evidence combination', detail: 'Combines multiple evidence sources with confidence weighting to produce a unified assessment of tiger identity and provenance.' },
  { name: '/explain-reasoning', description: 'Chain-of-thought documentation', detail: 'Documents the reasoning process step-by-step, creating an audit trail for investigation decisions.' },
  { name: '/investigate-facility', description: 'Deep facility research', detail: 'Performs comprehensive research on a specific facility, including USDA records, web presence, and social media activity.' },
  { name: '/generate-report', description: 'Audience-specific reports', detail: 'Generates investigation reports tailored to specific audiences: law enforcement, conservation organizations, internal teams, or the public.' },
  { name: '/assess-image', description: 'Image quality feedback', detail: 'Provides detailed quality assessment of tiger images, including blur level, resolution adequacy, lighting, and stripe visibility.' },
]

// API endpoints
const apiEndpoints = [
  { method: 'POST', path: '/api/investigations', description: 'Create a new investigation with an uploaded image' },
  { method: 'GET', path: '/api/investigations', description: 'List all investigations with pagination' },
  { method: 'GET', path: '/api/investigations/:id', description: 'Get investigation details and results' },
  { method: 'GET', path: '/api/investigations/:id/report', description: 'Download investigation report' },
  { method: 'GET', path: '/api/tigers', description: 'List all identified tigers with filters' },
  { method: 'GET', path: '/api/tigers/:id', description: 'Get tiger details, images, and sighting history' },
  { method: 'GET', path: '/api/facilities', description: 'List all tracked facilities' },
  { method: 'GET', path: '/api/facilities/:id', description: 'Get facility details with associated tigers' },
  { method: 'GET', path: '/api/dashboard/stats', description: 'Get dashboard statistics overview' },
  { method: 'GET', path: '/api/models/available', description: 'List available ML models and their status' },
  { method: 'POST', path: '/api/models/benchmark', description: 'Run performance benchmark on a model' },
  { method: 'GET', path: '/api/verification', description: 'Get pending verification tasks' },
  { method: 'POST', path: '/api/verification/:id', description: 'Submit verification decision' },
  { method: 'GET', path: '/api/analytics/investigations', description: 'Investigation analytics with date range' },
  { method: 'GET', path: '/api/analytics/tigers', description: 'Tiger identification analytics' },
  { method: 'GET', path: '/api/analytics/facilities', description: 'Facility analytics and distribution' },
]

const Documentation = () => {
  const navigate = useNavigate()
  const [activeSection, setActiveSection] = useState('getting-started')
  const [showScrollTop, setShowScrollTop] = useState(false)

  const handleScroll = useCallback(() => {
    const scrollContainer = document.getElementById('doc-content')
    if (!scrollContainer) return

    setShowScrollTop(scrollContainer.scrollTop > 300)

    // Update active section based on scroll position
    for (const section of tocSections) {
      const el = document.getElementById(section.id)
      if (el) {
        const rect = el.getBoundingClientRect()
        if (rect.top <= 150 && rect.bottom > 0) {
          setActiveSection(section.id)
        }
      }
    }
  }, [])

  useEffect(() => {
    const scrollContainer = document.getElementById('doc-content')
    if (scrollContainer) {
      scrollContainer.addEventListener('scroll', handleScroll)
      return () => scrollContainer.removeEventListener('scroll', handleScroll)
    }
  }, [handleScroll])

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setActiveSection(id)
    }
  }

  const scrollToTop = () => {
    const scrollContainer = document.getElementById('doc-content')
    if (scrollContainer) {
      scrollContainer.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  const methodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'success' as const
      case 'POST': return 'info' as const
      case 'PUT': return 'warning' as const
      case 'DELETE': return 'danger' as const
      default: return 'default' as const
    }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]" data-testid="documentation-page">
      {/* Table of Contents Sidebar */}
      <aside className="hidden lg:block w-72 flex-shrink-0 border-r border-tactical-200 dark:border-tactical-700 bg-white dark:bg-tactical-900 overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center space-x-2 mb-6">
            <BookOpenIcon className="h-6 w-6 text-tiger-orange" />
            <h2 className="text-lg font-bold text-tactical-900 dark:text-tactical-100">Documentation</h2>
          </div>
          <nav className="space-y-1">
            {tocSections.map((section) => {
              const Icon = section.icon
              return (
                <button
                  key={section.id}
                  onClick={() => scrollToSection(section.id)}
                  className={`
                    w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left
                    ${
                      activeSection === section.id
                        ? 'bg-tiger-orange/10 text-tiger-orange dark:bg-tiger-orange/20'
                        : 'text-tactical-600 dark:text-tactical-400 hover:bg-tactical-100 dark:hover:bg-tactical-800 hover:text-tactical-900 dark:hover:text-tactical-200'
                    }
                  `}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <span>{section.label}</span>
                </button>
              )
            })}
          </nav>

          <div className="mt-8 pt-6 border-t border-tactical-200 dark:border-tactical-700">
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => navigate('/investigation2')}
            >
              <MagnifyingGlassCircleIcon className="h-4 w-4 mr-2" />
              Launch Investigation
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div id="doc-content" className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-8 space-y-12">
          {/* Page Header */}
          <div>
            <h1 className="text-3xl font-bold text-tactical-900 dark:text-tactical-100">Tiger ID Documentation</h1>
            <p className="text-tactical-600 dark:text-tactical-400 mt-2 text-lg">
              Comprehensive guide to the Tiger ID wildlife identification and anti-trafficking investigation system.
            </p>

            {/* Mobile TOC */}
            <div className="lg:hidden mt-6">
              <Card padding="sm">
                <p className="text-xs font-semibold text-tactical-500 dark:text-tactical-400 uppercase tracking-wider mb-3">On this page</p>
                <div className="flex flex-wrap gap-2">
                  {tocSections.map((section) => (
                    <button
                      key={section.id}
                      onClick={() => scrollToSection(section.id)}
                      className={`
                        px-3 py-1.5 rounded-full text-xs font-medium transition-colors
                        ${
                          activeSection === section.id
                            ? 'bg-tiger-orange text-white'
                            : 'bg-tactical-100 dark:bg-tactical-800 text-tactical-600 dark:text-tactical-400 hover:bg-tactical-200 dark:hover:bg-tactical-700'
                        }
                      `}
                    >
                      {section.label}
                    </button>
                  ))}
                </div>
              </Card>
            </div>
          </div>

          {/* ==================== GETTING STARTED ==================== */}
          <section id="getting-started">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 rounded-lg bg-tiger-orange/10 dark:bg-tiger-orange/20">
                <RocketLaunchIcon className="h-6 w-6 text-tiger-orange" />
              </div>
              <h2 className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">Getting Started</h2>
            </div>

            <Card padding="lg">
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">What is Tiger ID?</h3>
                  <p className="text-tactical-700 dark:text-tactical-300 leading-relaxed">
                    Tiger ID is a wildlife identification system designed for tracking captive tigers using AI/ML re-identification.
                    It assists investigators in determining whether tigers are being trafficked or moved illicitly by analyzing
                    user-provided images against a known gallery of identified tigers. The system uses a 6-model machine learning
                    ensemble, web intelligence gathering, and Claude AI-powered analysis to produce comprehensive investigation reports.
                  </p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">Basic Workflow</h3>
                  <div className="space-y-4">
                    {[
                      { step: 1, title: 'Log In', desc: 'Access the system with your credentials. Contact your administrator if you need an account.' },
                      { step: 2, title: 'Navigate to Investigation', desc: 'Click "Investigation" in the sidebar or use the "Launch Investigation" button on the home page.' },
                      { step: 3, title: 'Upload an Image', desc: 'Upload a tiger image (JPEG, PNG, or WebP). The system will validate image quality automatically.' },
                      { step: 4, title: 'Monitor Progress', desc: 'Watch the 6-phase pipeline process your image in real time. Each phase provides live status updates.' },
                      { step: 5, title: 'Review Results', desc: 'Examine matched tigers, confidence scores, web intelligence findings, and the generated report.' },
                      { step: 6, title: 'Download Report', desc: 'Export a PDF report tailored to your audience (law enforcement, conservation, internal, or public).' },
                    ].map((item) => (
                      <div key={item.step} className="flex items-start space-x-4">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-tiger-orange text-white flex items-center justify-center text-sm font-bold">
                          {item.step}
                        </div>
                        <div>
                          <p className="font-semibold text-tactical-900 dark:text-tactical-100">{item.title}</p>
                          <p className="text-sm text-tactical-600 dark:text-tactical-400 mt-0.5">{item.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">Key Pages</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {[
                      { name: 'Home', path: '/', desc: 'System overview and quick actions' },
                      { name: 'Dashboard', path: '/dashboard', desc: 'Analytics and real-time metrics' },
                      { name: 'Investigation', path: '/investigation2', desc: 'Launch and monitor investigations' },
                      { name: 'Tigers', path: '/tigers', desc: 'Browse identified tiger gallery' },
                      { name: 'Facilities', path: '/facilities', desc: 'Track facilities and locations' },
                      { name: 'Verification', path: '/verification', desc: 'Review and verify match results' },
                      { name: 'Discovery', path: '/discovery', desc: 'Automated tiger discovery pipeline' },
                      { name: 'Model Weights', path: '/model-weights', desc: 'Configure ML ensemble weights' },
                    ].map((page) => (
                      <button
                        key={page.path}
                        onClick={() => navigate(page.path)}
                        className="flex items-center space-x-3 p-3 rounded-lg bg-tactical-50 dark:bg-tactical-800 hover:bg-tactical-100 dark:hover:bg-tactical-700 transition-colors text-left group"
                      >
                        <ChevronRightIcon className="h-4 w-4 text-tactical-400 group-hover:text-tiger-orange transition-colors" />
                        <div>
                          <p className="text-sm font-medium text-tactical-900 dark:text-tactical-100">{page.name}</p>
                          <p className="text-xs text-tactical-500 dark:text-tactical-400">{page.desc}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </section>

          {/* ==================== INVESTIGATION WORKFLOW ==================== */}
          <section id="investigation-workflow">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 rounded-lg bg-tiger-orange/10 dark:bg-tiger-orange/20">
                <MagnifyingGlassCircleIcon className="h-6 w-6 text-tiger-orange" />
              </div>
              <h2 className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">Investigation Workflow</h2>
            </div>

            <p className="text-tactical-700 dark:text-tactical-300 mb-6 leading-relaxed">
              Each investigation follows a 6-phase pipeline powered by LangGraph workflows. The phases execute
              sequentially, with each phase building on the results of the previous one. Real-time progress
              is streamed to the UI via WebSocket connections.
            </p>

            <div className="space-y-4">
              {workflowPhases.map((phase, index) => (
                <Card key={phase.key} padding="lg">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 rounded-full bg-tiger-orange text-white flex items-center justify-center font-bold text-lg">
                        {phase.phase}
                      </div>
                      {index < workflowPhases.length - 1 && (
                        <div className="w-0.5 h-6 bg-tactical-200 dark:bg-tactical-700 mx-auto mt-2" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">{phase.name}</h3>
                        <Badge variant="default" size="xs">
                          <code className="font-mono">{phase.key}</code>
                        </Badge>
                      </div>
                      <p className="text-tactical-700 dark:text-tactical-300 text-sm leading-relaxed mb-3">
                        {phase.description}
                      </p>
                      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                        {phase.details.map((detail) => (
                          <li key={detail} className="flex items-center space-x-2 text-sm text-tactical-600 dark:text-tactical-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-tiger-orange flex-shrink-0" />
                            <span>{detail}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </section>

          {/* ==================== TIGER DATABASE ==================== */}
          <section id="tiger-database">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 rounded-lg bg-tiger-orange/10 dark:bg-tiger-orange/20">
                <IdentificationIcon className="h-6 w-6 text-tiger-orange" />
              </div>
              <h2 className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">Tiger Database</h2>
            </div>

            <div className="space-y-6">
              <Card padding="lg">
                <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">How Tigers Are Identified</h3>
                <p className="text-tactical-700 dark:text-tactical-300 leading-relaxed mb-4">
                  Every tiger has a unique stripe pattern, similar to human fingerprints. Tiger ID extracts these patterns
                  using deep learning models that generate high-dimensional embedding vectors. These embeddings are stored
                  in a SQLite database with sqlite-vec for fast approximate nearest neighbor (ANN) search. When a new image
                  is submitted, its embedding is compared against all known tigers to find the closest matches.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-tactical-50 dark:bg-tactical-800">
                    <p className="text-sm font-semibold text-tactical-900 dark:text-tactical-100">6-Model Ensemble</p>
                    <p className="text-xs text-tactical-600 dark:text-tactical-400 mt-1">Multiple models cross-validate each identification for accuracy</p>
                  </div>
                  <div className="p-4 rounded-lg bg-tactical-50 dark:bg-tactical-800">
                    <p className="text-sm font-semibold text-tactical-900 dark:text-tactical-100">Vector Similarity</p>
                    <p className="text-xs text-tactical-600 dark:text-tactical-400 mt-1">sqlite-vec enables fast ANN search across 10k+ tiger gallery</p>
                  </div>
                  <div className="p-4 rounded-lg bg-tactical-50 dark:bg-tactical-800">
                    <p className="text-sm font-semibold text-tactical-900 dark:text-tactical-100">Confidence Scoring</p>
                    <p className="text-xs text-tactical-600 dark:text-tactical-400 mt-1">Weighted ensemble scores with calibration temperature per model</p>
                  </div>
                </div>
              </Card>

              <Card padding="lg">
                <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">Understanding Confidence Scores</h3>
                <div className="space-y-3">
                  {[
                    { range: '85%+', label: 'High Confidence', variant: 'success' as const, desc: 'Strong match. Multiple models agree with high similarity scores. Suitable for evidentiary purposes.' },
                    { range: '65-84%', label: 'Medium Confidence', variant: 'warning' as const, desc: 'Probable match. Some model disagreement. Manual verification recommended.' },
                    { range: '40-64%', label: 'Low Confidence', variant: 'orange' as const, desc: 'Possible match. Significant model disagreement. Additional images recommended for confirmation.' },
                    { range: '<40%', label: 'No Match', variant: 'danger' as const, desc: 'Unlikely match. The tiger is probably not in the database or image quality is insufficient.' },
                  ].map((item) => (
                    <div key={item.range} className="flex items-start space-x-4 p-3 rounded-lg bg-tactical-50 dark:bg-tactical-800">
                      <Badge variant={item.variant} size="sm" className="mt-0.5 flex-shrink-0 min-w-[80px] justify-center">
                        {item.range}
                      </Badge>
                      <div>
                        <p className="text-sm font-medium text-tactical-900 dark:text-tactical-100">{item.label}</p>
                        <p className="text-xs text-tactical-600 dark:text-tactical-400 mt-0.5">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </section>

          {/* ==================== FACILITIES ==================== */}
          <section id="facilities">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 rounded-lg bg-tiger-orange/10 dark:bg-tiger-orange/20">
                <BuildingOfficeIcon className="h-6 w-6 text-tiger-orange" />
              </div>
              <h2 className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">Facilities</h2>
            </div>

            <div className="space-y-6">
              <Card padding="lg">
                <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">Facility Tracking</h3>
                <p className="text-tactical-700 dark:text-tactical-300 leading-relaxed mb-4">
                  Tiger ID tracks facilities (zoos, sanctuaries, roadside exhibits, breeders) that house captive tigers.
                  Each facility record includes USDA license information, geographic location, associated tigers, and
                  historical data on tiger transfers.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {[
                    { field: 'Exhibitor Name', desc: 'Official USDA-registered name of the facility' },
                    { field: 'Location', desc: 'City, state, and geographic coordinates' },
                    { field: 'Tiger Count', desc: 'Number of tigers currently associated with the facility' },
                    { field: 'License Status', desc: 'Current USDA license status and inspection history' },
                    { field: 'Transfer History', desc: 'Record of tigers transferred to/from other facilities' },
                    { field: 'Web Presence', desc: 'Known websites, social media, and online listings' },
                  ].map((item) => (
                    <div key={item.field} className="p-3 rounded-lg bg-tactical-50 dark:bg-tactical-800">
                      <p className="text-sm font-semibold text-tactical-900 dark:text-tactical-100">{item.field}</p>
                      <p className="text-xs text-tactical-600 dark:text-tactical-400 mt-1">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </Card>

              <Card padding="lg">
                <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">Discovery Pipeline</h3>
                <p className="text-tactical-700 dark:text-tactical-300 leading-relaxed mb-4">
                  The Discovery Pipeline continuously monitors facility websites to automatically discover new tiger images.
                  It uses Playwright for JavaScript-heavy site rendering, respects per-domain rate limits, and deduplicates
                  images using SHA256 hashing before submitting them to the ML pipeline.
                </p>
                <div className="space-y-2">
                  {[
                    { label: 'Rate Limiting', value: 'Per-domain tracking with exponential backoff (2s base, 60s max)' },
                    { label: 'Image Deduplication', value: 'SHA256 hashing prevents re-processing known images' },
                    { label: 'Playwright Crawling', value: 'Auto-detection and rendering of JS-heavy sites' },
                    { label: 'ML Processing', value: 'Discovered images are automatically run through the 6-model ensemble' },
                  ].map((item) => (
                    <div key={item.label} className="flex items-start space-x-3 py-2 border-b border-tactical-100 dark:border-tactical-800 last:border-0">
                      <span className="text-sm font-medium text-tactical-900 dark:text-tactical-100 w-40 flex-shrink-0">{item.label}</span>
                      <span className="text-sm text-tactical-600 dark:text-tactical-400">{item.value}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </section>

          {/* ==================== ML ENSEMBLE ==================== */}
          <section id="ml-ensemble">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 rounded-lg bg-tiger-orange/10 dark:bg-tiger-orange/20">
                <CpuChipIcon className="h-6 w-6 text-tiger-orange" />
              </div>
              <h2 className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">ML Ensemble</h2>
            </div>

            <p className="text-tactical-700 dark:text-tactical-300 mb-6 leading-relaxed">
              Tiger ID uses a 6-model weighted ensemble for tiger re-identification. Each model generates a
              high-dimensional embedding vector from a tiger image, and these embeddings are compared against
              the known gallery using cosine similarity. GPU inference runs on Modal, while all other processing
              happens locally.
            </p>

            {/* Models Table */}
            <Card padding="none" className="mb-6">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-tactical-200 dark:divide-tactical-700">
                  <thead className="bg-tactical-50 dark:bg-tactical-800">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wider">Model</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wider">Weight</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wider">Embedding Dim</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wider">Cal. Temp</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wider">Description</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-tactical-900 divide-y divide-tactical-200 dark:divide-tactical-700">
                    {ensembleModels.map((model) => (
                      <tr key={model.name} className="hover:bg-tactical-50 dark:hover:bg-tactical-800 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <code className="text-sm font-mono font-medium text-tiger-orange">{model.name}</code>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            <div className="w-20 h-2 rounded-full bg-tactical-200 dark:bg-tactical-700 overflow-hidden">
                              <div
                                className="h-full rounded-full bg-tiger-orange"
                                style={{ width: `${model.weight * 250}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium text-tactical-900 dark:text-tactical-100">
                              {(model.weight * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-tactical-600 dark:text-tactical-400">
                          {model.embeddingDim.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-tactical-600 dark:text-tactical-400">
                          {model.calibrationTemp}
                        </td>
                        <td className="px-6 py-4 text-sm text-tactical-600 dark:text-tactical-400 max-w-xs">
                          {model.description}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Ensemble Modes */}
            <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-4">Ensemble Modes</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {ensembleModes.map((mode) => (
                <Card key={mode.key} padding="md">
                  <div className="flex items-center space-x-2 mb-2">
                    <h4 className="font-semibold text-tactical-900 dark:text-tactical-100">{mode.name}</h4>
                    {mode.key === 'weighted' && (
                      <Badge variant="tiger" size="xs">Recommended</Badge>
                    )}
                  </div>
                  <p className="text-sm text-tactical-700 dark:text-tactical-300 leading-relaxed mb-3">
                    {mode.description}
                  </p>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-medium text-tactical-500 dark:text-tactical-400">Best for:</span>
                    <span className="text-xs text-tactical-700 dark:text-tactical-300">{mode.best}</span>
                  </div>
                </Card>
              ))}
            </div>
          </section>

          {/* ==================== MCP SERVERS ==================== */}
          <section id="mcp-servers">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 rounded-lg bg-tiger-orange/10 dark:bg-tiger-orange/20">
                <ServerStackIcon className="h-6 w-6 text-tiger-orange" />
              </div>
              <h2 className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">MCP Servers</h2>
            </div>

            <p className="text-tactical-700 dark:text-tactical-300 mb-6 leading-relaxed">
              Tiger ID integrates 11 Model Context Protocol (MCP) servers that provide tool capabilities to the
              Claude AI agent during investigation workflows. These servers expose specialized functions for
              database operations, web research, image analysis, and report generation.
            </p>

            {/* Core Workflow Servers */}
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">
                  Core Workflow
                  <Badge variant="tiger" size="xs" className="ml-2">Investigation 2.0</Badge>
                </h3>
                <Card padding="none">
                  <div className="divide-y divide-tactical-200 dark:divide-tactical-700">
                    {mcpServers.core.map((server) => (
                      <div key={server.name} className="p-4 hover:bg-tactical-50 dark:hover:bg-tactical-800 transition-colors">
                        <div className="flex items-center space-x-2 mb-1">
                          <code className="text-sm font-mono font-medium text-tiger-orange">{server.name}</code>
                        </div>
                        <p className="text-sm text-tactical-700 dark:text-tactical-300">{server.description}</p>
                        <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-1">{server.purpose}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">Integration Servers</h3>
                <Card padding="none">
                  <div className="divide-y divide-tactical-200 dark:divide-tactical-700">
                    {mcpServers.integration.map((server) => (
                      <div key={server.name} className="p-4 hover:bg-tactical-50 dark:hover:bg-tactical-800 transition-colors">
                        <div className="flex items-center space-x-2 mb-1">
                          <code className="text-sm font-mono font-medium text-tiger-orange">{server.name}</code>
                        </div>
                        <p className="text-sm text-tactical-700 dark:text-tactical-300">{server.description}</p>
                        <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-1">{server.purpose}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">Browser Automation</h3>
                <Card padding="none">
                  <div className="divide-y divide-tactical-200 dark:divide-tactical-700">
                    {mcpServers.browser.map((server) => (
                      <div key={server.name} className="p-4 hover:bg-tactical-50 dark:hover:bg-tactical-800 transition-colors">
                        <div className="flex items-center space-x-2 mb-1">
                          <code className="text-sm font-mono font-medium text-tiger-orange">{server.name}</code>
                        </div>
                        <p className="text-sm text-tactical-700 dark:text-tactical-300">{server.description}</p>
                        <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-1">{server.purpose}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          </section>

          {/* ==================== SKILLS ==================== */}
          <section id="skills">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 rounded-lg bg-tiger-orange/10 dark:bg-tiger-orange/20">
                <SparklesIcon className="h-6 w-6 text-tiger-orange" />
              </div>
              <h2 className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">Skills</h2>
            </div>

            <p className="text-tactical-700 dark:text-tactical-300 mb-6 leading-relaxed">
              Tiger ID includes 5 Claude skills that provide specialized capabilities during investigations.
              Skills are invoked by the AI agent when specific expertise is needed and produce structured
              outputs that feed back into the investigation workflow.
            </p>

            <div className="space-y-4">
              {skills.map((skill) => (
                <Card key={skill.name} padding="md">
                  <div className="flex items-start space-x-4">
                    <code className="text-sm font-mono font-medium text-tiger-orange bg-tiger-orange/10 px-2 py-1 rounded flex-shrink-0">
                      {skill.name}
                    </code>
                    <div>
                      <p className="font-medium text-tactical-900 dark:text-tactical-100">{skill.description}</p>
                      <p className="text-sm text-tactical-600 dark:text-tactical-400 mt-1 leading-relaxed">{skill.detail}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </section>

          {/* ==================== API REFERENCE ==================== */}
          <section id="api-reference">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 rounded-lg bg-tiger-orange/10 dark:bg-tiger-orange/20">
                <CommandLineIcon className="h-6 w-6 text-tiger-orange" />
              </div>
              <h2 className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">API Reference</h2>
            </div>

            <p className="text-tactical-700 dark:text-tactical-300 mb-6 leading-relaxed">
              The Tiger ID backend exposes a RESTful API built with FastAPI. All endpoints require authentication
              via JWT bearer tokens unless otherwise noted. The API runs on port 8000 by default.
            </p>

            <Card padding="none">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-tactical-200 dark:divide-tactical-700">
                  <thead className="bg-tactical-50 dark:bg-tactical-800">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wider">Method</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wider">Endpoint</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wider">Description</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-tactical-900 divide-y divide-tactical-200 dark:divide-tactical-700">
                    {apiEndpoints.map((endpoint) => (
                      <tr key={`${endpoint.method}-${endpoint.path}`} className="hover:bg-tactical-50 dark:hover:bg-tactical-800 transition-colors">
                        <td className="px-6 py-3 whitespace-nowrap">
                          <Badge variant={methodColor(endpoint.method)} size="xs">
                            {endpoint.method}
                          </Badge>
                        </td>
                        <td className="px-6 py-3 whitespace-nowrap">
                          <code className="text-sm font-mono text-tactical-900 dark:text-tactical-100">{endpoint.path}</code>
                        </td>
                        <td className="px-6 py-3 text-sm text-tactical-600 dark:text-tactical-400">
                          {endpoint.description}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            <Card padding="lg" className="mt-6">
              <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">Authentication</h3>
              <p className="text-sm text-tactical-700 dark:text-tactical-300 leading-relaxed mb-4">
                All API requests must include a valid JWT token in the Authorization header. Tokens are obtained
                via the login endpoint and expire after the configured session duration.
              </p>
              <div className="bg-tactical-950 dark:bg-tactical-950 rounded-lg p-4 overflow-x-auto">
                <code className="text-sm text-tactical-300 font-mono whitespace-pre">{`curl -H "Authorization: Bearer <token>" \\
  http://localhost:8000/api/tigers`}</code>
              </div>
            </Card>

            <Card padding="lg" className="mt-4">
              <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-3">Tech Stack</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  { category: 'Backend', tech: 'Python 3.11, FastAPI, SQLAlchemy, SQLite + sqlite-vec' },
                  { category: 'Frontend', tech: 'React 18, TypeScript, Vite, TailwindCSS, RTK Query' },
                  { category: 'ML', tech: 'PyTorch, 6-model ReID ensemble, MegaDetector v5' },
                  { category: 'Infrastructure', tech: 'Modal (GPU inference), LangGraph (workflows)' },
                ].map((item) => (
                  <div key={item.category} className="p-3 rounded-lg bg-tactical-50 dark:bg-tactical-800">
                    <p className="text-sm font-semibold text-tactical-900 dark:text-tactical-100">{item.category}</p>
                    <p className="text-xs text-tactical-600 dark:text-tactical-400 mt-1">{item.tech}</p>
                  </div>
                ))}
              </div>
            </Card>
          </section>

          {/* Footer spacer */}
          <div className="h-12" />
        </div>
      </div>

      {/* Scroll to top button */}
      {showScrollTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-6 right-6 p-3 rounded-full bg-tiger-orange text-white shadow-lg hover:bg-tiger-orange-dark transition-colors z-50"
          aria-label="Scroll to top"
        >
          <ArrowUpIcon className="h-5 w-5" />
        </button>
      )}
    </div>
  )
}

export default Documentation
