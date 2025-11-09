# Supabase Migration Guide - SQLite to Supabase

This document provides all schema information, facilities data, file upload capabilities, and logs needed to migrate from SQLite to Supabase.

## Table of Contents
1. [Database Schema](#database-schema)
2. [Enum Types](#enum-types)
3. [Tables](#tables)
4. [File Upload & Storage](#file-upload--storage)
5. [Facilities](#facilities)
6. [Logs & Audit](#logs--audit)
7. [Migration Steps](#migration-steps)
8. [Supabase-Specific Considerations](#supabase-specific-considerations)

---

## Database Schema

### Prerequisites
- Enable `pgvector` extension for vector similarity search
- All UUIDs use PostgreSQL UUID type
- JSON columns use PostgreSQL JSONB type
- Vector embeddings use pgvector `vector(512)` type

---

## Enum Types

Create these enum types in Supabase:

```sql
CREATE TYPE tiger_status AS ENUM ('active', 'monitored', 'seized', 'deceased');
CREATE TYPE side_view AS ENUM ('left', 'right', 'both', 'unknown');
CREATE TYPE investigation_status AS ENUM ('draft', 'active', 'pending_verification', 'completed', 'archived', 'cancelled');
CREATE TYPE priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE evidence_source_type AS ENUM ('image', 'web_search', 'document', 'user_input');
CREATE TYPE entity_type AS ENUM ('tiger', 'facility', 'evidence', 'investigation');
CREATE TYPE verification_status AS ENUM ('pending', 'in_review', 'approved', 'rejected');
CREATE TYPE user_role AS ENUM ('investigator', 'analyst', 'supervisor', 'admin');
CREATE TYPE model_type AS ENUM ('detection', 'reid', 'pose');
```

---

## Tables

### 1. users
User account management

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'investigator',
    permissions JSONB DEFAULT '{}',
    department VARCHAR(100),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    api_key_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_username ON users(username);
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_role ON users(role);
```

### 2. facilities
Facility/exhibitor information

```sql
CREATE TABLE facilities (
    facility_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exhibitor_name VARCHAR(255) NOT NULL,
    usda_license VARCHAR(100),
    state VARCHAR(50),
    city VARCHAR(100),
    address TEXT,
    tiger_count INTEGER DEFAULT 0,
    tiger_capacity INTEGER,
    social_media_links JSONB DEFAULT '{}',
    website VARCHAR(500),
    ir_date TIMESTAMP,
    last_inspection_date TIMESTAMP,
    accreditation_status VARCHAR(100),
    violation_history JSONB DEFAULT '[]',
    last_crawled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    -- Reference data fields (from migration 003)
    is_reference_facility BOOLEAN DEFAULT FALSE NOT NULL,
    data_source VARCHAR(100),
    reference_dataset_version TIMESTAMP,
    reference_metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_facility_state ON facilities(state);
CREATE INDEX idx_facility_usda ON facilities(usda_license);
CREATE INDEX idx_facility_name ON facilities(exhibitor_name);
CREATE INDEX idx_facility_reference ON facilities(is_reference_facility);
CREATE INDEX idx_facility_data_source ON facilities(data_source);
```

### 3. tigers
Tiger individual records

```sql
CREATE TABLE tigers (
    tiger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    alias VARCHAR(255),
    origin_facility_id UUID REFERENCES facilities(facility_id),
    last_seen_location VARCHAR(255),
    last_seen_date TIMESTAMP,
    status tiger_status DEFAULT 'active',
    tags JSONB DEFAULT '[]',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tiger_status ON tigers(status);
CREATE INDEX idx_tiger_name ON tigers(name);
```

### 4. tiger_images
Tiger images with vector embeddings

```sql
CREATE TABLE tiger_images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tiger_id UUID REFERENCES tigers(tiger_id),
    image_path VARCHAR(500) NOT NULL,
    thumbnail_path VARCHAR(500),
    embedding vector(512),
    side_view side_view DEFAULT 'unknown',
    pose_keypoints JSONB,
    metadata JSONB DEFAULT '{}',
    quality_score FLOAT,
    verified BOOLEAN DEFAULT FALSE,
    uploaded_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_image_tiger ON tiger_images(tiger_id);
CREATE INDEX idx_image_verified ON tiger_images(verified);
-- HNSW index for vector similarity search
CREATE INDEX idx_image_embedding_hnsw ON tiger_images USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

### 5. investigations
Investigation records

```sql
CREATE TABLE investigations (
    investigation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(user_id),
    status investigation_status DEFAULT 'draft',
    priority priority DEFAULT 'medium',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    summary JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    assigned_to JSONB DEFAULT '[]',
    related_tigers JSONB DEFAULT '[]',
    related_facilities JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_investigation_status ON investigations(status);
CREATE INDEX idx_investigation_created_by ON investigations(created_by);
CREATE INDEX idx_investigation_priority ON investigations(priority);
```

### 6. investigation_steps
Investigation step/agent activity tracking

```sql
CREATE TABLE investigation_steps (
    step_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES investigations(investigation_id),
    step_type VARCHAR(100) NOT NULL,
    agent_name VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    result JSONB DEFAULT '{}',
    error_message TEXT,
    duration_ms INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    parent_step_id UUID REFERENCES investigation_steps(step_id)
);

CREATE INDEX idx_step_investigation ON investigation_steps(investigation_id);
CREATE INDEX idx_step_timestamp ON investigation_steps(timestamp);
```

### 7. evidence
Evidence items linked to investigations

```sql
CREATE TABLE evidence (
    evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES investigations(investigation_id),
    source_type evidence_source_type NOT NULL,
    source_url VARCHAR(500),
    content JSONB DEFAULT '{}',
    extracted_text TEXT,
    relevance_score FLOAT,
    verified BOOLEAN DEFAULT FALSE,
    verified_by UUID REFERENCES users(user_id),
    verification_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_evidence_investigation ON evidence(investigation_id);
CREATE INDEX idx_evidence_source_type ON evidence(source_type);
CREATE INDEX idx_evidence_verified ON evidence(verified);
```

### 8. verification_queue
Verification queue for entities requiring review

```sql
CREATE TABLE verification_queue (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type entity_type NOT NULL,
    entity_id UUID NOT NULL,
    priority priority DEFAULT 'medium',
    requires_human_review BOOLEAN DEFAULT TRUE,
    assigned_to UUID REFERENCES users(user_id),
    reviewed_by UUID REFERENCES users(user_id),
    status verification_status DEFAULT 'pending',
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP
);

CREATE INDEX idx_queue_status ON verification_queue(status);
CREATE INDEX idx_queue_priority ON verification_queue(priority);
CREATE INDEX idx_queue_entity ON verification_queue(entity_type, entity_id);
```

### 9. user_sessions
User session management

```sql
CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_session_user ON user_sessions(user_id);
CREATE INDEX idx_session_expires ON user_sessions(expires_at);
```

### 10. investigation_templates
Investigation workflow templates

```sql
CREATE TABLE investigation_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_steps JSONB DEFAULT '[]',
    default_agents JSONB DEFAULT '[]',
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 11. saved_searches
Saved search queries

```sql
CREATE TABLE saved_searches (
    search_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    name VARCHAR(255) NOT NULL,
    search_criteria JSONB DEFAULT '{}',
    alert_enabled BOOLEAN DEFAULT FALSE,
    last_executed TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 12. investigation_comments
Comments on investigations

```sql
CREATE TABLE investigation_comments (
    comment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES investigations(investigation_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    content TEXT NOT NULL,
    parent_comment_id UUID REFERENCES investigation_comments(comment_id),
    created_at TIMESTAMP DEFAULT NOW(),
    edited_at TIMESTAMP
);
```

### 13. investigation_annotations
Annotations on investigations/evidence

```sql
CREATE TABLE investigation_annotations (
    annotation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES investigations(investigation_id),
    evidence_id UUID REFERENCES evidence(evidence_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    annotation_type VARCHAR(100) NOT NULL,
    coordinates JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 14. evidence_links
Links between evidence items

```sql
CREATE TABLE evidence_links (
    link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_evidence_id UUID NOT NULL REFERENCES evidence(evidence_id),
    target_evidence_id UUID NOT NULL REFERENCES evidence(evidence_id),
    link_type VARCHAR(100) NOT NULL,
    strength FLOAT,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 15. model_versions
ML model version tracking

```sql
CREATE TABLE model_versions (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    model_type model_type NOT NULL,
    version VARCHAR(50) NOT NULL,
    path VARCHAR(500) NOT NULL,
    training_data_hash VARCHAR(100),
    metrics JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_model_name ON model_versions(model_name);
CREATE INDEX idx_model_type ON model_versions(model_type);
CREATE INDEX idx_model_active ON model_versions(is_active);
```

**Note:** The migration file (002_additional_tables.py) doesn't include `model_name` column, but the model definition does. Ensure this column exists.

### 16. model_inferences
Model inference logging

```sql
CREATE TABLE model_inferences (
    inference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES model_versions(model_id),
    input_data_hash VARCHAR(100),
    output JSONB DEFAULT '{}',
    confidence FLOAT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_inference_model ON model_inferences(model_id);
CREATE INDEX idx_inference_timestamp ON model_inferences(created_at);
```

### 17. notifications
User notifications

```sql
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    related_entity_type VARCHAR(100),
    related_entity_id UUID,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notification_user ON notifications(user_id);
CREATE INDEX idx_notification_read ON notifications(read);
CREATE INDEX idx_notification_created ON notifications(created_at);
```

### 18. background_jobs
Background job tracking

```sql
CREATE TABLE background_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}',
    result JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_job_type ON background_jobs(job_type);
CREATE INDEX idx_job_status ON background_jobs(status);
CREATE INDEX idx_job_started ON background_jobs(started_at);
```

### 19. data_exports
Data export tracking

```sql
CREATE TABLE data_exports (
    export_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    export_type VARCHAR(100) NOT NULL,
    filters JSONB DEFAULT '{}',
    file_path VARCHAR(500),
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX idx_export_user ON data_exports(user_id);
CREATE INDEX idx_export_status ON data_exports(status);
CREATE INDEX idx_export_expires ON data_exports(expires_at);
```

### 20. system_metrics
System performance metrics

```sql
CREATE TABLE system_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    tags JSONB DEFAULT '{}'
);

CREATE INDEX idx_metric_name ON system_metrics(metric_name);
CREATE INDEX idx_metric_timestamp ON system_metrics(timestamp);
```

### 21. feedback
User feedback

```sql
CREATE TABLE feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID REFERENCES investigations(investigation_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    feedback_type VARCHAR(100) NOT NULL,
    content JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 22. crawl_history
Web crawling history for facilities

```sql
CREATE TABLE crawl_history (
    crawl_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id UUID REFERENCES facilities(facility_id),
    source_url VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL,
    images_found INTEGER DEFAULT 0,
    tigers_identified INTEGER DEFAULT 0,
    crawled_at TIMESTAMP DEFAULT NOW(),
    -- Enhanced fields from migration 003
    pages_crawled INTEGER DEFAULT 0,
    total_content_size INTEGER,
    crawl_duration_ms INTEGER,
    error_message TEXT,
    error_log JSONB DEFAULT '[]',
    retry_count INTEGER DEFAULT 0,
    content_changes_detected BOOLEAN DEFAULT FALSE,
    change_summary JSONB DEFAULT '{}',
    crawl_statistics JSONB DEFAULT '{}',
    completed_at TIMESTAMP
);

CREATE INDEX idx_crawl_facility ON crawl_history(facility_id);
CREATE INDEX idx_crawl_timestamp ON crawl_history(crawled_at);
CREATE INDEX idx_crawl_status ON crawl_history(status);
```

### 23. password_reset_tokens
Password reset token management

```sql
CREATE TABLE password_reset_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reset_token_user ON password_reset_tokens(user_id);
CREATE INDEX idx_reset_token_token ON password_reset_tokens(token);
```

### 24. audit_logs
Comprehensive audit logging

```sql
CREATE TABLE audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    action_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    action_details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action_type);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at);
CREATE INDEX idx_audit_status ON audit_logs(status);
```

---

## File Upload & Storage

### Current Storage Implementation

**Storage Type:** Local filesystem (configurable to S3)

**Storage Path:** `./data/storage` (default, configurable via `STORAGE_PATH`)

**Storage Structure:**
```
data/
├── storage/
│   └── tigers/
│       └── {tiger_id}/
│           ├── {index}_{filename}
│           └── thumbnails/
├── models/
│   └── atrw/
│       └── images/
│           └── {tiger_id}/
└── datasets/
```

### File Upload Endpoints

1. **Tiger Image Upload** (`POST /api/tigers`)
   - Stores images in `data/storage/tigers/{tiger_id}/`
   - Creates `TigerImage` records with `image_path` and `thumbnail_path`
   - Generates vector embeddings (512 dimensions)
   - Supports multiple images per request

2. **Evidence Upload** (`POST /api/investigations/{investigation_id}/evidence/upload`)
   - Stores files temporarily for processing
   - Uses MarkitDown for document extraction
   - Auto-detects tigers in images
   - Stores metadata in `evidence.content` JSONB field

### Migration to Supabase Storage

**Supabase Storage Buckets Needed:**

1. **`tiger-images`** - Tiger photos
   - Public: No (authenticated access)
   - Allowed MIME types: `image/jpeg`, `image/png`, `image/webp`
   - Max file size: 10MB

2. **`evidence-files`** - Investigation evidence
   - Public: No
   - Allowed MIME types: `image/*`, `application/pdf`, `text/*`
   - Max file size: 50MB

3. **`thumbnails`** - Image thumbnails
   - Public: Yes (for faster loading)
   - Allowed MIME types: `image/jpeg`, `image/png`
   - Max file size: 1MB

**Storage Path Migration:**

Current paths like `data/storage/tigers/{tiger_id}/{filename}` should become:
- Supabase Storage paths: `tiger-images/{tiger_id}/{filename}`
- Or use Supabase Storage URLs: `https://{project}.supabase.co/storage/v1/object/public/tiger-images/{tiger_id}/{filename}`

**Code Changes Required:**

1. Update `backend/config/settings.py`:
   ```python
   class StorageSettings(BaseSettings):
       type: str = Field(default="supabase", alias="STORAGE_TYPE")
       supabase_url: str = Field(alias="SUPABASE_URL")
       supabase_key: str = Field(alias="SUPABASE_SERVICE_ROLE_KEY")
       bucket_tiger_images: str = "tiger-images"
       bucket_evidence: str = "evidence-files"
       bucket_thumbnails: str = "thumbnails"
   ```

2. Create storage service adapter for Supabase Storage API

3. Update `TigerImage.image_path` to store Supabase Storage paths/URLs

---

## Facilities

### Facility Data Structure

Facilities contain comprehensive information about tiger exhibitors:

**Key Fields:**
- `exhibitor_name` - Facility name
- `usda_license` - USDA license number
- `state`, `city`, `address` - Location
- `tiger_count`, `tiger_capacity` - Tiger population
- `social_media_links` - JSONB with platform URLs
- `website` - Facility website
- `accreditation_status` - Accreditation information
- `violation_history` - JSONB array of violations
- `is_reference_facility` - Flag for reference datasets
- `data_source` - Source of facility data
- `reference_metadata` - Additional reference data

**Facility Import:**

Facilities can be imported from:
- Excel files (`scripts/import_reference_facilities.py`)
- USDA API
- Non-accredited facilities dataset (`data/datasets/non-accredited-facilities`)

**Facility Relationships:**
- One-to-many with `tigers` (via `origin_facility_id`)
- One-to-many with `crawl_history` (web crawling records)

**Facility Endpoints:**
- `GET /api/facilities` - List facilities (supports pagination)
- `GET /api/facilities/{facility_id}` - Get facility details
- `POST /api/facilities/import-excel` - Import from Excel
- `POST /api/facilities` - Create facility

---

## Logs & Audit

### Audit Logs (`audit_logs` table)

Comprehensive audit trail for all system actions:

**Fields:**
- `user_id` - User who performed action (nullable)
- `action_type` - Type of action (e.g., 'investigation_created', 'evidence_added')
- `resource_type` - Type of resource affected ('investigation', 'evidence', 'tiger', 'facility')
- `resource_id` - ID of affected resource
- `action_details` - JSONB with additional details
- `ip_address` - User IP address
- `user_agent` - Browser/client information
- `status` - Action status ('success', 'failed', 'error')
- `error_message` - Error details if failed
- `created_at` - Timestamp

**Indexes:**
- `idx_audit_user` - User-based queries
- `idx_audit_action` - Action type queries
- `idx_audit_resource` - Resource-based queries
- `idx_audit_created` - Time-based queries
- `idx_audit_status` - Status filtering

**Audit Service:**
- `backend/services/audit_service.py` - `AuditService.log_action()`
- Used throughout the application for tracking actions

### Application Logs

**File-based Logging:**
- `logs/app.log` - General application logs
- `logs/error.log` - Error logs only
- Rotating file handler (10MB max, 5 backups)

**Logging Configuration:**
- `backend/utils/logging.py` - Centralized logging setup
- Uses `structlog` for structured logging
- Logs to both files and console

**Migration to Supabase:**

For production, consider:
1. **Supabase Logs** - Use Supabase's built-in logging (limited retention)
2. **External Service** - Integrate with logging service (e.g., Logtail, Datadog)
3. **Database Logs Table** - Store critical logs in `audit_logs` table

### Model Inference Logs (`model_inferences` table)

Tracks ML model usage:
- `model_id` - Reference to model version
- `input_data_hash` - Hash of input data
- `output` - JSONB with model output
- `confidence` - Prediction confidence
- `execution_time_ms` - Performance metric
- `created_at` - Timestamp

**Service:** `backend/services/model_inference_logger.py`

### Investigation Steps (`investigation_steps` table)

Tracks agent workflow execution:
- `step_type` - Type of step ('research', 'analysis', 'validation', 'reporting')
- `agent_name` - Agent that executed step
- `status` - Step status ('completed', 'in_progress', 'failed')
- `result` - JSONB with step results
- `duration_ms` - Execution time
- `error_message` - Error details if failed

---

## Migration Steps

### 1. Enable Extensions in Supabase

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Create Enum Types

Run all enum type creation statements from [Enum Types](#enum-types) section.

### 3. Create Tables

Create all tables in dependency order:
1. `users` (no dependencies)
2. `facilities` (no dependencies)
3. `tigers` (depends on `facilities`)
4. `tiger_images` (depends on `tigers`, `users`)
5. `investigations` (depends on `users`)
6. `investigation_steps` (depends on `investigations`)
7. `evidence` (depends on `investigations`, `users`)
8. All other tables following foreign key dependencies

### 4. Create Indexes

Create all indexes as specified in table definitions.

### 5. Set Up Supabase Storage

```sql
-- Create storage buckets
INSERT INTO storage.buckets (id, name, public)
VALUES 
    ('tiger-images', 'tiger-images', false),
    ('evidence-files', 'evidence-files', false),
    ('thumbnails', 'thumbnails', true);

-- Set up storage policies (Row Level Security)
-- Example for tiger-images bucket:
CREATE POLICY "Users can upload tiger images"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'tiger-images');

CREATE POLICY "Users can read tiger images"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'tiger-images');
```

### 6. Migrate Data from SQLite

**Option A: Using Python Script**

```python
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import json

# Connect to SQLite
sqlite_conn = sqlite3.connect('data/production.db')
sqlite_conn.row_factory = sqlite3.Row

# Connect to Supabase PostgreSQL
supabase_conn = psycopg2.connect(
    host="your-project.supabase.co",
    database="postgres",
    user="postgres",
    password="your-password",
    port=5432
)

# Migrate each table
tables = [
    'users', 'facilities', 'tigers', 'tiger_images',
    'investigations', 'investigation_steps', 'evidence',
    # ... all other tables
]

for table in tables:
    # Read from SQLite
    sqlite_cursor = sqlite_conn.execute(f"SELECT * FROM {table}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        continue
    
    # Convert to list of dicts
    data = [dict(row) for row in rows]
    
    # Handle JSON fields
    for row in data:
        for key, value in row.items():
            if isinstance(value, str) and (key.endswith('_links') or key in ['permissions', 'tags', 'content', 'metadata']):
                try:
                    row[key] = json.loads(value)
                except:
                    pass
    
    # Insert into Supabase
    # ... (implementation depends on table structure)
```

**Option B: Using pgLoader**

```bash
pgloader sqlite://data/production.db postgresql://user:pass@host:5432/dbname
```

**Option C: Export/Import CSV**

1. Export SQLite data to CSV
2. Import CSV into Supabase using Supabase dashboard or `psql`

### 7. Migrate File Storage

1. **Upload files to Supabase Storage:**
   ```python
   from supabase import create_client, Client
   
   supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
   
   # Upload each file
   for tiger_image in tiger_images:
       local_path = tiger_image['image_path']
       storage_path = f"tiger-images/{tiger_id}/{filename}"
       
       with open(local_path, 'rb') as f:
           supabase.storage.from_('tiger-images').upload(
               storage_path,
               f.read()
           )
       
       # Update database record with new path
       update_image_path(tiger_image['image_id'], storage_path)
   ```

2. **Update database paths** to reference Supabase Storage URLs/paths

### 8. Update Application Configuration

Update `.env`:
```env
USE_POSTGRESQL=true
DATABASE_URL=postgresql://postgres:[password]@[project].supabase.co:5432/postgres
STORAGE_TYPE=supabase
SUPABASE_URL=https://[project].supabase.co
SUPABASE_SERVICE_ROLE_KEY=[service-role-key]
```

### 9. Update Code for Supabase Storage

Create `backend/services/supabase_storage.py`:
```python
from supabase import create_client, Client
from pathlib import Path
from typing import Optional

class SupabaseStorageService:
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
    
    def upload_tiger_image(self, tiger_id: str, file_path: Path, file_data: bytes) -> str:
        storage_path = f"tiger-images/{tiger_id}/{file_path.name}"
        self.client.storage.from_('tiger-images').upload(storage_path, file_data)
        return storage_path
    
    def get_image_url(self, storage_path: str, bucket: str = 'tiger-images') -> str:
        return self.client.storage.from_(bucket).get_public_url(storage_path)
```

---

## Supabase-Specific Considerations

### 1. Row Level Security (RLS)

Enable RLS policies for sensitive tables:

```sql
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence ENABLE ROW LEVEL SECURITY;

-- Example policy: Users can only see their own investigations
CREATE POLICY "Users can view own investigations"
ON investigations FOR SELECT
TO authenticated
USING (created_by = auth.uid());
```

### 2. Vector Similarity Search

Supabase supports pgvector. Use cosine similarity:

```sql
-- Find similar tiger images
SELECT tiger_id, image_id, 
       1 - (embedding <=> query_embedding) as similarity
FROM tiger_images
WHERE 1 - (embedding <=> query_embedding) > 0.7
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

### 3. Real-time Subscriptions

Supabase supports real-time subscriptions:

```javascript
// Subscribe to investigation updates
const channel = supabase
  .channel('investigations')
  .on('postgres_changes', 
    { event: 'UPDATE', schema: 'public', table: 'investigations' },
    (payload) => console.log('Investigation updated:', payload)
  )
  .subscribe();
```

### 4. Database Functions

Create helper functions:

```sql
-- Function to update facility tiger count
CREATE OR REPLACE FUNCTION update_facility_tiger_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE facilities
    SET tiger_count = (
        SELECT COUNT(*) FROM tigers 
        WHERE origin_facility_id = NEW.origin_facility_id
    )
    WHERE facility_id = NEW.origin_facility_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tiger_count_update
AFTER INSERT OR UPDATE OR DELETE ON tigers
FOR EACH ROW EXECUTE FUNCTION update_facility_tiger_count();
```

### 5. Connection Pooling

Use Supabase connection pooling:
- Direct connection: `postgresql://...`
- Pooled connection: `postgresql://[project].pooler.supabase.com:6543/postgres`

### 6. Backup & Restore

- Supabase provides automatic daily backups
- Manual backups via Supabase dashboard
- Point-in-time recovery available

---

## Verification Checklist

- [ ] All enum types created
- [ ] All tables created with correct columns
- [ ] All indexes created
- [ ] Foreign key constraints in place
- [ ] pgvector extension enabled
- [ ] HNSW index created for `tiger_images.embedding`
- [ ] Storage buckets created
- [ ] Storage policies configured
- [ ] Data migrated from SQLite
- [ ] File storage migrated to Supabase Storage
- [ ] Application configuration updated
- [ ] Code updated for Supabase Storage
- [ ] RLS policies configured (if needed)
- [ ] Database functions created (if needed)
- [ ] Connection pooling configured
- [ ] Backup strategy in place

---

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Supabase Storage Documentation](https://supabase.com/docs/guides/storage)
- [Supabase Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)

---

## Notes

1. **Model Versions Table**: The migration file doesn't include `model_name` column, but the model definition does. Ensure this column exists in Supabase.

2. **Vector Embeddings**: The `tiger_images.embedding` column uses `vector(512)`. Ensure pgvector extension is enabled before creating this table.

3. **JSON Fields**: All JSON fields use PostgreSQL JSONB type for better performance and indexing capabilities.

4. **Timestamps**: All timestamp fields use `TIMESTAMP` type. Consider using `TIMESTAMPTZ` for timezone-aware timestamps if needed.

5. **File Paths**: Current implementation uses local filesystem paths. Migration requires updating all `image_path` and `thumbnail_path` values to Supabase Storage paths/URLs.

6. **Audit Logs**: The `audit_logs` table is separate from the older `audit_log` table (if it exists). Use `audit_logs` as the primary audit table.

