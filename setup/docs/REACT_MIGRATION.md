# React Migration - Complete Reference

## Migration Status: ✅ COMPLETE

The Tiger ID frontend has been successfully migrated from Streamlit to React.

---

## What Changed

### Before (Streamlit)
- Python-based UI (port 8501)
- Server-side rendering
- Limited customization

### After (React)
- TypeScript + React SPA (port 5173)
- Client-side rendering
- Modern design system
- Real-time WebSocket communication
- Redux state management

---

## New Frontend Structure

```
frontend/
├── src/
│   ├── app/              # Redux store & RTK Query API
│   ├── components/       # Reusable UI components
│   ├── pages/            # 14 page components
│   ├── features/         # Redux slices (auth, investigations, tigers, notifications)
│   ├── hooks/            # Custom hooks (useAuth, useWebSocket, useDebounce)
│   ├── utils/            # Utilities (api-client, formatters, cn)
│   └── types/            # TypeScript type definitions
├── Dockerfile            # Production build
├── nginx.conf            # Nginx configuration
└── package.json          # Dependencies
```

---

## Technology Stack

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS
- Redux Toolkit + RTK Query
- React Router v6
- WebSocket (native)
- Recharts (charts)

**Backend Enhancements:**
- Native WebSocket support
- Enhanced CORS
- Standardized API responses
- Pagination helpers

---

## All Pages Migrated (14/14)

1. Login & Password Reset
2. Home
3. Dashboard
4. Investigations
5. Investigation Workspace
6. Launch Investigation
7. Tigers
8. Facilities
9. Verification
10. Investigation Tools
11. Templates
12. Saved Searches

---

## Key Features

- ✅ JWT authentication
- ✅ Real-time WebSocket updates
- ✅ Responsive design
- ✅ Form validation (Zod)
- ✅ Error boundaries
- ✅ Loading states
- ✅ Optimistic UI updates
- ✅ API caching

---

## Docker Integration

All Docker configurations updated:
- `docker-compose.yml` - Production
- `docker-compose.dev.yml` - Development
- `docker-compose.quickstart.yml` - All-in-one
- `docker/entrypoint.sh` - Auto-setup (migrations + user)

---

## Development

```bash
cd frontend
npm run dev      # Start dev server
npm run build    # Production build
npm run test     # Unit tests
npm run test:e2e # E2E tests
```

---

For complete setup instructions, see `setup/docs/SETUP_GUIDE.md`

