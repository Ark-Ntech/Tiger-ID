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

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

