# Tiger ID Frontend

React-based frontend for the Tiger Trafficking Investigation System.

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Redux Toolkit + RTK Query
- **Routing**: React Router v6
- **Forms**: React Hook Form + Zod validation
- **UI Components**: Headless UI
- **Icons**: Hero Icons
- **Charts**: Recharts
- **WebSocket**: Native WebSocket API

## Development

### Prerequisites

- Node.js 18+ and npm
- Running backend API on port 8000

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create a `.env` file:

```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── app/            # Redux store and API configuration
│   ├── components/     # Reusable components
│   │   ├── common/    # Basic UI components
│   │   ├── layout/    # Layout components
│   │   └── investigations/ # Investigation-specific components
│   ├── features/      # Redux slices
│   ├── hooks/         # Custom React hooks
│   ├── pages/         # Page components
│   ├── types/         # TypeScript type definitions
│   ├── utils/         # Utility functions
│   ├── App.tsx        # Main app component
│   ├── main.tsx       # Entry point
│   └── index.css      # Global styles
├── Dockerfile         # Production Docker image
├── nginx.conf         # Nginx configuration
└── vite.config.ts     # Vite configuration
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run test` - Run tests (Vitest)
- `npm run test:e2e` - Run E2E tests (Playwright)

## Docker

### Development

```bash
# Build and run with docker-compose
docker-compose up frontend
```

### Production

```bash
# Build production image
docker build -t tiger-id-frontend .

# Run production container
docker run -p 80:80 tiger-id-frontend
```

## Features

- **Authentication**: JWT-based authentication with login/logout
- **Dashboard**: Real-time statistics and analytics
- **Investigations**: Create, manage, and track investigations
- **Tiger Database**: View and search identified tigers
- **Facilities**: Monitor tiger facilities
- **Verification**: Review and verify evidence
- **Real-time Updates**: WebSocket-based real-time communication
- **Responsive Design**: Mobile-friendly UI

---

## Component Architecture

### Investigation 2.0 Components

Located in `src/components/investigations/`:

| Component | Purpose |
|-----------|---------|
| `Investigation2Upload` | Image upload with drag-and-drop |
| `Investigation2Progress` | Phase progress indicator |
| `Investigation2ResultsEnhanced` | Match results with tabs |
| `Investigation2MatchCard` | Individual tiger match display |
| `Investigation2Methodology` | Reasoning chain visualization |
| `Investigation2Citations` | Evidence citations panel |
| `Investigation2Map` | Location mapping |
| `ReportDownload` | Multi-format report export |

### Common Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `ErrorBoundary` | `common/` | React error boundary |
| `ProtectedRoute` | `auth/` | Authentication guard |
| `Layout` | `layout/` | Main app layout with navigation |

---

## State Management

### Redux Store Structure

The store is configured in `src/app/store.ts` with 4 slices plus RTK Query:

```typescript
{
  api: RTKQueryReducer,      // RTK Query cache
  auth: authReducer,         // Authentication state
  investigations: investigationsReducer,  // Investigation workflow state
  tigers: tigersReducer,     // Tiger database state
  notifications: notificationsReducer    // UI notifications
}
```

### Slices

| Slice | File | State |
|-------|------|-------|
| `auth` | `features/auth/authSlice.ts` | `user`, `token`, `isAuthenticated` |
| `investigations` | `features/investigations/investigationsSlice.ts` | `currentInvestigation`, `phase`, `results` |
| `tigers` | `features/tigers/tigersSlice.ts` | `selectedTiger`, `filters` |
| `notifications` | `features/notifications/notificationsSlice.ts` | `messages`, `unreadCount` |

### Typed Hooks

Use typed hooks from `src/app/hooks.ts`:

```typescript
import { useAppDispatch, useAppSelector } from '../app/hooks'

const dispatch = useAppDispatch()
const user = useAppSelector((state) => state.auth.user)
```

---

## RTK Query API

### Configuration

API is defined in `src/app/api.ts` with base URL from environment:

```typescript
import { api } from '../app/api'

// Use generated hooks
const { data, isLoading, error } = useGetTigersQuery()
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | User authentication |
| `/investigation2/run` | POST | Start investigation workflow |
| `/investigation2/status/{id}` | GET | Get investigation status |
| `/tigers` | GET | List all tigers |
| `/tigers/{id}` | GET | Get tiger details |
| `/facilities` | GET | List all facilities |

### Cache Invalidation

RTK Query handles caching automatically. Tags used:
- `Tiger` - Tiger records
- `Facility` - Facility records
- `Investigation` - Investigation results

---

## Routing

### Route Table

| Path | Component | Auth Required |
|------|-----------|---------------|
| `/login` | `Login` | No |
| `/password-reset` | `PasswordReset` | No |
| `/` | `Home` | Yes |
| `/dashboard` | `Dashboard` | Yes |
| `/investigation2` | `Investigation2` | Yes |
| `/tigers` | `Tigers` | Yes |
| `/tigers/:id` | `TigerDetail` | Yes |
| `/facilities` | `Facilities` | Yes |
| `/facilities/:id` | `FacilityDetail` | Yes |
| `/model-weights` | `ModelWeights` | Yes |
| `/finetuning` | `FineTuning` | Yes |
| `/dataset-management` | `DatasetManagement` | Yes |
| `/verification` | `Verification` | Yes |
| `/search` | `SearchResults` | Yes |
| `*` | `NotFound` | No |

### Redirects

Legacy routes redirect to Investigation 2.0:
- `/investigations` → `/investigation2`
- `/tools` → `/investigation2`
- `/model-testing` → `/investigation2`
- `/model-dashboard` → `/dashboard`

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

