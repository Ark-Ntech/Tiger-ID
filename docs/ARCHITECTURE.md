# System Architecture

## Table of Contents

- [Overview](#overview)
- [Architecture Diagram](#architecture-diagram)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Deployment Architecture](#deployment-architecture)
- [Scalability Considerations](#scalability-considerations)
- [Security Architecture](#security-architecture)
- [Monitoring & Observability](#monitoring--observability)

## Overview

The Tiger Trafficking Investigation System is a comprehensive multi-agent investigative platform that combines AI orchestration, computer vision, web intelligence, and collaborative workflows to assist investigators in detecting and analyzing tiger trafficking activities.

## Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["Frontend Layer"]
        UI[React Frontend]
        UI --> Home[Home Page]
        UI --> InvList[Investigations List]
        UI --> InvWorkspace[Investigation Workspace]
        UI --> InvTools[Investigation Tools]
        UI --> Tigers[Tigers]
        UI --> Facilities[Facilities]
        UI --> Dashboard[Dashboard]
        UI --> Search[Search]
        UI --> Verify[Verification Queue]
    end

    subgraph API["FastAPI Backend"]
        Auth["Authentication & Authorization<br/>JWT, RBAC, CSRF"]
        Agents[Multi-Agent Orchestration System]
        WebIntel[Web Intelligence Services]
        CVModels[Computer Vision Models]
        Services[Business Logic Services]
        Jobs[Background Jobs Celery]
        
        Agents --> Orch[Orchestrator Agent]
        Agents --> Research[Research Agent]
        Agents --> Analysis[Analysis Agent]
        Agents --> Validate[Validation Agent]
        Agents --> Report[Reporting Agent]
    end

    subgraph Data["Data Layer"]
        PG[("PostgreSQL<br/>pgvector<br/>Embeddings<br/>Audit Logs")]
        Redis[("Redis<br/>Cache<br/>Sessions<br/>Job Queue")]
    end

    subgraph External["External Services"]
        USDA[USDA API]
        CITES[CITES API]
        USFWS[USFWS API]
        Firecrawl[Firecrawl API]
        YouTube[YouTube API]
        Meta[Meta/Facebook API]
    end

    UI -->|HTTP/REST API| Agents
    UI -->|SSE| Agents
    UI -->|WebSocket| Agents
    Agents --> Auth
    Agents --> WebIntel
    Agents --> CVModels
    Agents --> Services
    Agents --> Jobs
    Services --> PG
    Services --> Redis
    WebIntel --> Firecrawl
    WebIntel --> YouTube
    WebIntel --> Meta
    Services --> USDA
    Services --> CITES
    Services --> USFWS
```

## Core Components

### 1. Frontend (React/TypeScript)

**Purpose:** User interface for investigators to interact with the system.

**Key Pages:**
- **Home**: Dashboard with activity feed and quick actions
- **Investigations**: List and manage investigations
- **Investigation Workspace**: Detailed investigation view with chat, timeline, relationships, and evidence
- **Investigation Tools**: Web search, image search, news monitoring, lead generation, etc.
- **Tigers**: Tiger identification and management
- **Facilities**: Facility information and monitoring
- **Dashboard**: Analytics and metrics visualization
- **Search**: Global search across all entities
- **Verification Queue**: Human-in-the-loop verification

**Technology Stack:**
- React 18+
- TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- Recharts/Plotly for visualizations

### 2. Backend API (FastAPI)

**Purpose:** RESTful API providing all backend functionality.

**Key Features:**
- RESTful API design
- JWT authentication
- Server-Sent Events (SSE) for real-time updates
- Rate limiting (60 requests/minute per IP)
- CSRF protection (optional, via env var)
- Audit logging middleware
- CORS middleware
- Comprehensive error handling

**API Router Structure (16 route modules):**
- `/api/auth` - Authentication endpoints
- `/api/v1` - Core API endpoints  
- `/api/v1/investigations` - Investigation management and tools
- `/api/v1/search` - Global search
- `/api/v1/analytics` - Analytics endpoints
- `/api/v1/export` - Export functionality
- `/api/v1/audit` - Audit log endpoints (admin only)
- `/api/v1/notifications` - Notification endpoints
- `/api/v1/events` - Event history endpoints
- `/api/v1/sse` - Server-Sent Events for real-time updates
- `/api/v1/websocket` - WebSocket for real-time communication
- `/api/v1/verification` - Verification task endpoints
- `/api/v1/annotations` - Annotation endpoints
- `/api/v1/templates` - Template management
- `/api/v1/saved-searches` - Saved search management
- `/api/integrations` - External API integrations

### 3. Multi-Agent Orchestration System

**Purpose:** Coordinate specialized AI agents to perform comprehensive investigations.

**Agents:**

#### OrchestratorAgent
- Coordinates entire investigation workflow
- Manages agent execution sequence
- Emits events for real-time updates
- Handles error recovery and retries
- Integrates with NotificationService

#### ResearchAgent
- Gathers information from various sources
- Web search capabilities
- Reverse image search
- News monitoring
- Lead generation
- Reference facility checking
- Social media intelligence (YouTube, Meta/Facebook)
- Auto-links evidence to investigations

#### AnalysisAgent
- Analyzes collected evidence
- Detects contradictions
- Assesses trafficking probability
- Evidence strength evaluation

#### ValidationAgent
- Validates findings
- Detects hallucinations
- Cross-validates evidence
- Overall confidence assessment

#### ReportingAgent
- Compiles investigation reports
- Generates summaries
- Creates recommendations

**Agent Communication:**
- Event-driven architecture
- Shared database state
- Tool-based interaction via MCP (Model Context Protocol)
- Optional Langgraph StateGraph workflow (enabled via `USE_LANGGRAPH` env var)

**MCP Servers:**
- **FirecrawlMCPServer**: Web search and scraping tools
- **DatabaseMCPServer**: Database query tools
- **TigerIDMCPServer**: Tiger identification tools
- **YouTubeMCPServer**: YouTube Data API v3 tools (video search, channel info, comments)
- **MetaMCPServer**: Meta Graph API tools (page search, posts, comments)

**Workflow Orchestration:**

- **OrchestratorAgent**: Custom orchestrator pattern (default)
  - Sequential execution of investigation phases
  - Direct agent coordination
  - Built-in error handling and recovery

- **InvestigationWorkflow (Langgraph)**: Optional Langgraph StateGraph implementation
  - State-based workflow management
  - Conditional routing between phases
  - Graph-based execution with checkpoints
  - Enable via `USE_LANGGRAPH=true` environment variable

### 4. Web Intelligence Services

**Purpose:** Gather intelligence from web sources.

**Services:**
- **WebSearchService**: Multi-provider web search (Serper, Tavily, Perplexity)
- **ImageSearchService**: Reverse image search
- **NewsMonitoringService**: Automated news article monitoring
- **LeadGenerationService**: Discovery of suspicious listings/activities
- **RelationshipAnalysisService**: Entity relationship extraction and link analysis
- **EvidenceCompilationService**: Evidence extraction, scoring, and grouping
- **CrawlSchedulerService**: Configurable crawl scheduling
- **YouTubeClient**: YouTube Data API v3 integration for video and channel intelligence
- **MetaClient**: Meta Graph API integration for Facebook page and post intelligence

### 5. Computer Vision Models

**Purpose:** Detect and identify tigers in images.

**Models:**
- **MegaDetector v5**: Wildlife detection model for cropping tigers
- **Tiger Re-ID Model**: Siamese network for stripe pattern matching
- **Vector Search**: pgvector for similarity search

**Model Pipeline:**

```mermaid
flowchart LR
    A[Image Uploaded] --> B[MegaDetector<br/>Detects Tiger]
    B --> C[Tiger Cropped<br/>from Image]
    C --> D[Re-ID Model<br/>Extracts Features]
    D --> E[Embedding Vector<br/>Generated]
    E --> F[Vector Search<br/>pgvector]
    F --> G[Similar Tigers<br/>Found]
    G --> H[Confidence<br/>Calculated]
    H --> I[Results Returned]
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9
    style E fill:#fff9c4
    style F fill:#fce4ec
    style G fill:#e0f2f1
    style H fill:#fff3e0
    style I fill:#c8e6c9
```

### 6. Database Layer (PostgreSQL)

**Purpose:** Persistent data storage with vector search capabilities.

**Key Tables:**
- `users` - User accounts and authentication
- `investigations` - Investigation records
- `investigation_steps` - Investigation workflow steps
- `evidence` - Evidence items linked to investigations
- `tigers` - Tiger records
- `tiger_images` - Tiger images with embeddings
- `facilities` - Facility information
- `crawl_history` - Web crawl history
- `notifications` - User notifications
- `audit_logs` - System audit trail
- `verification_queue` - Human verification queue

**Extensions:**
- `pgvector` - Vector similarity search for embeddings
- Various indexes for performance optimization

### 7. Caching Layer (Redis)

**Purpose:** Improve performance through caching.

**Use Cases:**
- Web search results caching
- Model inference result caching
- Session storage
- Celery job queue

**Fallback:** In-memory cache if Redis unavailable

### 8. Background Jobs (Celery)

**Purpose:** Asynchronous task processing.

**Job Types:**
- News monitoring (scheduled)
- Data synchronization (USDA, CITES, USFWS)
- Web crawling (scheduled)
- Model batch inference

### 9. Security & Infrastructure

**Security Features:**
- JWT authentication
- CSRF protection (optional)
- Rate limiting
- Audit logging
- Password hashing (bcrypt)
- Input sanitization

**Infrastructure:**
- Connection pooling
- Query optimization hooks
- Slow query logging
- Error tracking (Sentry integration)
- Health check endpoints

## Data Flow

### Investigation Workflow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Orchestrator
    participant Research
    participant Analysis
    participant Validation
    participant Reporting
    participant Database

    User->>API: Create Investigation
    API->>Database: Store Investigation Record
    
    User->>API: Launch Investigation
    API->>Orchestrator: Initialize Workflow
    Orchestrator->>Orchestrator: Parse Inputs (Images, Text, Files)
    
    Orchestrator->>Research: Research Phase
    Research->>Research: Web Searches
    Research->>Research: Image Searches
    Research->>Research: News Monitoring
    Research->>Research: Lead Generation
    Research->>Database: Store Evidence
    
    Research-->>Orchestrator: Evidence Collected
    Orchestrator->>Analysis: Analysis Phase
    Analysis->>Analysis: Detect Contradictions
    Analysis->>Analysis: Assess Trafficking Probability
    Analysis->>Analysis: Evaluate Evidence Strength
    
    Analysis-->>Orchestrator: Analysis Complete
    Orchestrator->>Validation: Validation Phase
    Validation->>Validation: Validate Findings
    Validation->>Validation: Detect Hallucinations
    Validation->>Validation: Cross-validate Evidence
    
    Validation-->>Orchestrator: Validation Complete
    Orchestrator->>Reporting: Reporting Phase
    Reporting->>Reporting: Compile Report
    Reporting->>Reporting: Generate Summary
    Reporting->>Reporting: Create Recommendations
    Reporting->>Database: Store Report
    
    Reporting-->>Orchestrator: Report Complete
    Orchestrator->>API: Investigation Completed
    API->>User: Send Notifications
```

### Tiger Identification Workflow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant MegaDetector
    participant ReID
    participant Database
    participant VectorSearch

    User->>API: Upload Image
    API->>MegaDetector: Process Image
    MegaDetector->>MegaDetector: Detect Tiger
    MegaDetector->>MegaDetector: Crop Tiger Region
    MegaDetector-->>API: Cropped Tiger Image
    
    API->>ReID: Extract Features
    ReID->>ReID: Generate Embedding Vector
    ReID-->>API: Embedding Vector
    
    API->>VectorSearch: Search Similar Tigers
    VectorSearch->>Database: Query pgvector
    Database-->>VectorSearch: Similar Tigers
    VectorSearch->>VectorSearch: Calculate Confidence Scores
    VectorSearch-->>API: Top Matches with Scores
    
    API->>User: Return Results
```

### Real-time Updates

```mermaid
sequenceDiagram
    participant Agent
    participant EventService
    participant SSE
    participant Client
    participant UI

    Agent->>EventService: Emit Event
    EventService->>EventService: Broadcast Event
    EventService->>SSE: Stream Event
    SSE->>Client: SSE Update
    Client->>UI: Update UI
    UI->>UI: React State Update
    UI->>User: Display Progress
```

## Technology Stack

### Frontend
- **React** 18+ - Web application framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tooling and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts/Plotly** - Interactive charts

### Backend
- **FastAPI** 0.109+ - API framework
- **SQLAlchemy** 2.0+ - ORM
- **Alembic** - Database migrations
- **Celery** - Background jobs
- **Redis** - Caching and job queue

### AI/ML
- **PyTorch** - Deep learning framework
- **Transformers** - Pre-trained models
- **OmniVinci** (NVIDIA) - Multi-modal LLM orchestrator
- **MegaDetector v5** - Wildlife detection
- **Custom Siamese Networks** - Tiger Re-ID

### Database
- **PostgreSQL** 15+ - Primary database
- **pgvector** - Vector similarity search

### Protocols
- **MCP (Model Context Protocol)** - Tool integration
- **JWT** - Authentication tokens
- **SSE (Server-Sent Events)** - Real-time updates
- **Langgraph** - Optional workflow orchestration (enabled via USE_LANGGRAPH env var)

## Deployment Architecture

### Development

```mermaid
graph TB
    subgraph Dev["Development Environment"]
        DevAPI[FastAPI<br/>Local:8000]
        DevUI[React<br/>Local:5173]
        DevWorker[Celery Worker<br/>Local]
    end
    
    subgraph Docker["Docker Compose"]
        DevPostgres[(PostgreSQL<br/>5432)]
        DevRedis[(Redis<br/>6379)]
    end
    
    DevAPI --> DevPostgres
    DevAPI --> DevRedis
    DevWorker --> DevPostgres
    DevWorker --> DevRedis
    DevUI --> DevAPI
    
    style Dev fill:#e3f2fd
    style Docker fill:#fff3e0
```

**Characteristics:**
- All services run locally
- Docker Compose for infrastructure (PostgreSQL, Redis)
- Development mode with hot reloading

### Production

```mermaid
graph TB
    subgraph LB["Load Balancer"]
        Nginx[Nginx<br/>Reverse Proxy<br/>SSL/TLS]
    end
    
    subgraph App["Application Layer"]
        API1[FastAPI<br/>Instance 1]
        API2[FastAPI<br/>Instance 2]
        UI[React Frontend]
    end
    
    subgraph Workers["Worker Layer"]
        Worker1[Celery Worker 1]
        Worker2[Celery Worker 2]
        WorkerN[Celery Worker N]
    end
    
    subgraph Data["Data Layer"]
        PG[(PostgreSQL<br/>Master)]
        PGReplica[(PostgreSQL<br/>Read Replica)]
        Redis[(Redis<br/>Cluster)]
    end
    
    subgraph Storage["Storage"]
        S3[S3 Bucket<br/>Models & Data]
    end
    
    Nginx --> API1
    Nginx --> API2
    Nginx --> UI
    API1 --> PG
    API2 --> PG
    API1 --> Redis
    API2 --> Redis
    UI --> API1
    UI --> API2
    
    Worker1 --> PG
    Worker2 --> PG
    WorkerN --> PG
    Worker1 --> Redis
    Worker2 --> Redis
    WorkerN --> Redis
    
    API1 --> PGReplica
    API2 --> PGReplica
    
    API1 --> S3
    API2 --> S3
    Worker1 --> S3
    
    style LB fill:#ffebee
    style App fill:#e3f2fd
    style Workers fill:#fff3e0
    style Data fill:#e8f5e9
    style Storage fill:#f3e5f5
```

**Characteristics:**
- Docker containers for all services
- Reverse proxy (Nginx) for routing
- SSL/TLS encryption
- Load balancing for API (optional)
- Horizontal scaling for Celery workers
- Persistent storage for models and data

## Scalability Considerations

1. **API Scaling**: Multiple API instances behind load balancer
2. **Worker Scaling**: Horizontal scaling of Celery workers
3. **Database Scaling**: Connection pooling, read replicas (future)
4. **Cache Scaling**: Redis cluster (future)
5. **Model Inference**: Batch processing, GPU allocation

## Security Architecture

```mermaid
graph TB
    subgraph Security["Security Layers"]
        Auth[JWT Authentication]
        Auth --> RBAC[Role-Based Access Control]
        RBAC --> RateLimit[Rate Limiting<br/>60 req/min]
        RateLimit --> CSRF[CSRF Protection<br/>Optional]
        CSRF --> Validation[Input Validation<br/>Pydantic]
        Validation --> Sanitize[Input Sanitization]
        Sanitize --> Audit[Audit Logging]
    end
    
    subgraph Crypto["Cryptography"]
        Hash[Password Hashing<br/>bcrypt]
        Encrypt[Token Encryption]
    end
    
    subgraph Network["Network Security"]
        HTTPS[HTTPS/TLS]
        CORS[CORS Configuration]
        Headers[Security Headers]
    end
    
    Auth --> Hash
    Auth --> Encrypt
    RateLimit --> HTTPS
    CSRF --> CORS
    Validation --> Headers
    
    style Security fill:#ffebee
    style Crypto fill:#e3f2fd
    style Network fill:#fff3e0
```

**Key Security Features:**
1. **Authentication**: JWT tokens with expiration
2. **Authorization**: Role-based access control (RBAC)
3. **Input Validation**: Pydantic models, input sanitization
4. **CSRF Protection**: Token-based CSRF protection
5. **Rate Limiting**: Per-IP rate limiting
6. **Audit Logging**: Comprehensive audit trail
7. **Error Tracking**: Sentry integration for error monitoring
8. **Secure Storage**: Password hashing, encrypted tokens

## Monitoring & Observability

```mermaid
graph LR
    subgraph Monitoring["Monitoring Stack"]
        Health[Health Checks<br/>/api/health]
        Metrics[Application Metrics<br/>System Metrics Table]
        Logs[Audit Logs<br/>audit_logs table]
        Events[Event Tracking<br/>Investigation Events]
        Errors[Error Tracking<br/>Sentry]
        DBLogs[Slow Query Logging<br/>Database Performance]
    end
    
    subgraph Alerting["Alerting"]
        Alerts[Alerts & Notifications]
    end
    
    Health --> Alerts
    Metrics --> Alerts
    Logs --> Alerts
    Events --> Alerts
    Errors --> Alerts
    DBLogs --> Alerts
    
    style Monitoring fill:#e8f5e9
    style Alerting fill:#ffebee
```

**Monitoring Components:**
1. **Health Checks**: `/api/health` endpoint
2. **Audit Logs**: All actions logged to `audit_logs` table
3. **Application Metrics**: System metrics table
4. **Error Tracking**: Sentry for error monitoring
5. **Slow Query Logging**: Database query performance tracking
6. **Event Tracking**: Investigation workflow events

