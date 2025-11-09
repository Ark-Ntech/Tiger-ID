# Supabase Setup Guide for Tiger-ID

This guide will walk you through setting up Tiger-ID with Supabase as the PostgreSQL database backend.

## Prerequisites

- A Supabase account (free tier works fine)
- Python 3.8+
- Node.js 16+
- Git

## Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Fill in your project details:
   - **Project Name**: `tiger-id` (or your preferred name)
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose closest to your location
   - **Pricing Plan**: Free tier is sufficient for development
4. Click "Create new project" and wait 2-3 minutes for provisioning

## Step 2: Get Your Database Connection String

1. In your Supabase project dashboard, click on the **Settings** icon (gear icon) in the left sidebar
2. Navigate to **Database** section
3. Scroll down to **Connection string** section
4. Select **URI** tab
5. Copy the connection string - it will look like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
6. Replace `[YOUR-PASSWORD]` with the database password you set in Step 1

## Step 3: Run Database Setup Script

We've created an automated setup script that will:
- Create all required tables with proper schemas
- Set up indexes for performance
- Create a default admin user
- Import facility data

1. Clone the repository:
   ```bash
   cd /path/to/your/projects
   git clone <repository-url>
   cd Tiger-ID
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the setup script:
   ```bash
   python scripts/setup_supabase.py
   ```

4. When prompted, enter your Supabase connection string (from Step 2)

5. The script will:
   - ✅ Test database connection
   - ✅ Create all tables (users, tigers, facilities, investigations, evidence, etc.)
   - ✅ Create admin user (username: `admin`, password: `admin123`)
   - ✅ Import 159 facilities from TPC dataset
   - ✅ Generate `.env` configuration file

## Step 4: Verify Database Setup

1. Go back to your Supabase dashboard
2. Click on **Table Editor** in the left sidebar
3. You should see all tables created:
   - `users`
   - `tigers`
   - `tiger_images`
   - `facilities`
   - `investigations`
   - `investigation_steps`
   - `evidence`
   - `audit_logs`
   - `verification_queue`
   - And more...

4. Click on the `facilities` table - you should see 159 rows imported
5. Click on the `users` table - you should see the admin user

## Step 5: Configure Environment Variables

The setup script automatically creates a `.env` file in the project root. Verify it contains:

```bash
# Database Mode (REQUIRED)
USE_POSTGRESQL=true
USE_SQLITE_DEMO=false

# Supabase Database (REQUIRED)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Security Keys (REQUIRED)
SECRET_KEY=change-me-in-production-generate-strong-random-key
JWT_SECRET_KEY=change-me-in-production-generate-strong-random-key

# Application Config
APP_ENV=development
DEBUG=true

# Storage
STORAGE_TYPE=local
STORAGE_PATH=./data/storage

# Redis (Optional - for background jobs)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Feature Flags
USE_LANGGRAPH=false
MFA_ENABLED=false
PROMETHEUS_ENABLED=false
LOG_LEVEL=INFO
```

**Important**: For production deployments, generate new secure random keys:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 6: Start the Backend

1. Make sure you're in the Tiger-ID directory
2. Start the backend server:
   ```bash
   cd /path/to/Tiger-ID
   python -m uvicorn backend.api.app:app --host 0.0.0.0 --port 8001 --reload
   ```

3. You should see:
   ```
   Using PostgreSQL database
   INFO:     Uvicorn running on http://0.0.0.0:8001
   Database connection successful
   Database has 159 facilities and 0 tigers
   API startup complete
   ```

4. Test the API:
   ```bash
   curl http://localhost:8001/health
   ```

   You should get a response showing database status as "healthy"

## Step 7: Start the Frontend

1. Open a new terminal window
2. Navigate to the frontend directory:
   ```bash
   cd /path/to/Tiger-ID/frontend
   ```

3. Install dependencies (first time only):
   ```bash
   npm install
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

5. The frontend will start on `http://localhost:5173` (or 5174 if 5173 is busy)

6. Open your browser and navigate to the URL shown in the terminal

## Step 8: Login and Verify

1. Open the application in your browser
2. Login with the default admin credentials:
   - **Username**: `admin`
   - **Password**: `admin123`

3. Navigate to the **Facilities** page
4. You should see all 159 facilities loaded from the TPC dataset

5. Navigate to the **Dashboard** page
6. You should see analytics showing:
   - 159 Facilities Tracked
   - 0 Tigers Identified (until you add tiger data)
   - 0 Active Investigations
   - etc.

## Troubleshooting

### "Connection refused" or "Socket hang up" errors

**Problem**: Frontend can't connect to backend API

**Solution**:
1. Make sure the backend is running on port 8001:
   ```bash
   lsof -ti:8001
   ```
2. If you see multiple processes, kill them and restart:
   ```bash
   kill -9 $(lsof -ti:8001)
   cd /path/to/Tiger-ID
   python -m uvicorn backend.api.app:app --host 0.0.0.0 --port 8001 --reload
   ```

### "No such table" errors

**Problem**: Database tables weren't created properly

**Solution**:
1. Re-run the setup script:
   ```bash
   python scripts/setup_supabase.py
   ```
2. When prompted, confirm you want to recreate tables

### "Invalid input syntax for type integer" when importing facilities

**Problem**: CSV data has float values (like "2.0") for integer columns

**Solution**: This is already fixed in the latest version. If you encounter this, make sure you're using the latest code.

### Slow query performance

**Problem**: Queries to Supabase taking 1-2 seconds each

**Solution**: We've implemented several optimizations:
1. **Query batching**: Multiple COUNT queries combined into single SQL statement
2. **Response caching**: Dashboard data cached for 5 minutes
3. **Connection pooling**: Reduced pool size to 5 connections

The dashboard should load in ~2 seconds on first load, then instantly on subsequent loads.

## Production Deployment Checklist

Before deploying to production:

- [ ] Generate new SECRET_KEY and JWT_SECRET_KEY
- [ ] Change default admin password
- [ ] Set `APP_ENV=production`
- [ ] Set `DEBUG=false`
- [ ] Enable HTTPS/TLS for database connection
- [ ] Configure proper CORS origins (not `*`)
- [ ] Set up Redis for caching (optional but recommended)
- [ ] Configure backup strategy for Supabase database
- [ ] Set up monitoring and error tracking (Sentry)
- [ ] Review and adjust rate limiting settings
- [ ] Enable MFA for admin accounts

## Data Import

### Importing Facility Data

The setup script automatically imports the TPC Tigers facility dataset (159 facilities).

If you need to import additional facility data:

1. Prepare your Excel file with the following columns:
   - Exhibitor (facility name)
   - License (USDA license number)
   - State
   - City (optional)
   - Address (optional)
   - Tigers (tiger count)
   - Website (optional)
   - Facebook, Instagram, TikTok, YouTube, TripAdvisor, Yelp (optional social media links)

2. Use the import script:
   ```bash
   python scripts/import_facilities.py /path/to/your/file.xlsx
   ```

### Importing Tiger Images

To add tiger images for identification:

1. Place tiger images in `data/models/atrw/images/`
2. Use the tiger import script (if available) or upload via the web interface

## Supabase Features

### Real-time Subscriptions (Optional)

Tiger-ID can leverage Supabase real-time features for live updates:

1. In Supabase dashboard, go to **Database** → **Replication**
2. Enable replication for tables you want to monitor in real-time
3. Update frontend code to use Supabase real-time subscriptions

### Row Level Security (RLS)

For production, consider enabling RLS:

1. Go to **Authentication** → **Policies**
2. Enable RLS for each table
3. Create policies for different user roles (admin, investigator, viewer)

### Automatic Backups

Supabase Pro tier includes:
- Daily automatic backups
- Point-in-time recovery
- Consider upgrading for production use

## Architecture Overview

```
┌─────────────────┐
│   Frontend      │
│   (React +      │
│   Vite)         │
│   Port 5173     │
└────────┬────────┘
         │ HTTP/REST
         │
┌────────▼────────┐
│   Backend API   │
│   (FastAPI)     │
│   Port 8001     │
└────────┬────────┘
         │ PostgreSQL
         │ Connection
         │
┌────────▼────────┐
│   Supabase      │
│   PostgreSQL    │
│   (Cloud)       │
└─────────────────┘
```

## Performance Characteristics

With Supabase free tier:
- **Query latency**: 1-2 seconds per query (depends on location)
- **Concurrent connections**: 5 (configurable via DB_POOL_SIZE)
- **Dashboard load time**: ~2 seconds (first load), instant (cached)
- **Facility list**: ~2-3 seconds to load 159 facilities
- **Storage**: 500 MB database, 1 GB file storage

## Support and Resources

- **Supabase Documentation**: https://supabase.com/docs
- **Tiger-ID Issues**: https://github.com/your-org/tiger-id/issues
- **Supabase Community**: https://github.com/supabase/supabase/discussions
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

## Next Steps

After setup is complete:

1. Explore the application features
2. Import tiger image data for identification
3. Create investigation workflows
4. Set up user accounts for your team
5. Configure external API integrations (USDA, CITES, USFWS)
6. Customize dashboard analytics

## What Changed in the Supabase Migration

### Database Connection (`backend/database/connection.py`)
- Added PostgreSQL connection using SQLAlchemy
- Configured connection pooling (pool_size=5, max_overflow=10)
- Handles Supabase-specific connection parameters

### Optimizations Added

1. **Dashboard Optimization** (`backend/api/dashboard_routes.py`)
   - New batched endpoint: `/api/v1/dashboard/stats`
   - Combines 20+ separate COUNT queries into 1 SQL statement
   - Reduces dashboard load time from 20-40 seconds to ~2 seconds

2. **Response Caching** (`backend/services/simple_cache.py`)
   - In-memory cache with configurable TTL (default 5 minutes)
   - Applied to expensive analytics queries
   - Dramatically improves perceived performance

3. **Facilities Import** (`scripts/import_facilities.py`)
   - Transforms Excel data to match Supabase schema
   - Handles data type conversions (float → integer)
   - Combines multiple social media columns into JSON field
   - Generates proper UUIDs for all records

### Schema Compatibility
All existing SQLAlchemy models work with both SQLite (local dev) and PostgreSQL (Supabase production) without modifications.

---

**Last Updated**: 2025-11-09
**Tiger-ID Version**: 1.0.0
**Supported Supabase Version**: PostgreSQL 15.x
