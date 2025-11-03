# API Documentation

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: Configure via environment variables

## Authentication

Most endpoints require authentication via JWT tokens. Include the token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

Login endpoint: `POST /api/auth/login`

```json
{
  "username": "user@example.com",
  "password": "password123",
  "remember_me": false
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "user_id": "...",
    "username": "user@example.com",
    "email": "user@example.com",
    "role": "investigator"
  }
}
```

## API Endpoints

### Authentication Endpoints

#### `POST /api/auth/login`
Login and receive JWT token.

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "password123",
  "remember_me": false
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": { ... }
}
```

#### `POST /api/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword123",
  "full_name": "New User"
}
```

**Response:** `201 Created`
```json
{
  "user_id": "...",
  "username": "newuser",
  "email": "newuser@example.com",
  "message": "User registered successfully"
}
```

#### `GET /api/auth/me`
Get current user information.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "user_id": "...",
  "username": "user@example.com",
  "email": "user@example.com",
  "role": "investigator",
  "is_active": true
}
```

#### `POST /api/auth/logout`
Logout current user (invalidates token).

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

#### `POST /api/auth/password-reset/request`
Request password reset.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

#### `POST /api/auth/password-reset/confirm`
Confirm password reset with token.

**Request Body:**
```json
{
  "token": "reset-token",
  "new_password": "newsecurepassword123"
}
```

### Investigation Endpoints

#### `POST /api/v1/investigations`
Create a new investigation.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "Investigation Title",
  "description": "Investigation description",
  "priority": "high",
  "tags": ["tag1", "tag2"]
}
```

**Response:** `201 Created`
```json
{
  "investigation_id": "...",
  "title": "Investigation Title",
  "status": "draft",
  "created_at": "2025-01-15T10:00:00Z"
}
```

#### `GET /api/v1/investigations`
List investigations (with filters).

**Query Parameters:**
- `status` (optional): Filter by status (draft, active, completed, etc.)
- `priority` (optional): Filter by priority (low, medium, high, critical)
- `limit` (optional, default: 50): Maximum results
- `offset` (optional, default: 0): Pagination offset

**Response:** `200 OK`
```json
{
  "investigations": [...],
  "count": 10,
  "total": 25
}
```

#### `GET /api/v1/investigations/{investigation_id}`
Get investigation details.

**Response:** `200 OK`
```json
{
  "investigation_id": "...",
  "title": "Investigation Title",
  "description": "...",
  "status": "active",
  "priority": "high",
  "evidence": [...],
  "steps": [...]
}
```

#### `POST /api/v1/investigations/{investigation_id}/launch`
Launch an investigation (starts orchestrator workflow).

**Request Body:**
```json
{
  "text": "Initial investigation input",
  "images": ["base64-encoded-image"],
  "files": []
}
```

**Response:** `200 OK`
```json
{
  "investigation_id": "...",
  "status": "in_progress",
  "message": "Investigation launched successfully"
}
```

#### `POST /api/v1/investigations/{investigation_id}/pause`
Pause an active investigation.

**Response:** `200 OK`
```json
{
  "investigation_id": "...",
  "status": "paused",
  "message": "Investigation paused successfully"
}
```

#### `POST /api/v1/investigations/{investigation_id}/resume`
Resume a paused investigation.

**Response:** `200 OK`
```json
{
  "investigation_id": "...",
  "status": "active",
  "message": "Investigation resumed successfully"
}
```

#### `POST /api/v1/investigations/{investigation_id}/cancel`
Cancel an investigation.

**Response:** `200 OK`
```json
{
  "investigation_id": "...",
  "status": "cancelled",
  "message": "Investigation cancelled successfully"
}
```

### Investigation Tools Endpoints

#### `POST /api/v1/investigations/search/web`
Perform web search.

**Request Body:**
```json
{
  "query": "tiger trafficking",
  "limit": 10,
  "provider": "serper"
}
```

**Response:** `200 OK`
```json
{
  "results": [
    {
      "title": "...",
      "url": "...",
      "snippet": "..."
    }
  ],
  "provider": "serper",
  "count": 10
}
```

#### `POST /api/v1/investigations/search/reverse-image`
Perform reverse image search.

**Request Body:**
```json
{
  "image_url": "https://example.com/image.jpg"
}
```

#### `POST /api/v1/investigations/search/news`
Search news articles.

**Request Body:**
```json
{
  "query": "tiger trafficking",
  "limit": 20
}
```

#### `POST /api/v1/investigations/generate-leads`
Generate investigation leads.

**Request Body:**
```json
{
  "keywords": ["tiger", "trafficking"],
  "sources": ["web", "news"]
}
```

#### `POST /api/v1/investigations/analyze-relationships`
Analyze entity relationships.

**Request Body:**
```json
{
  "entities": [
    {"type": "facility", "id": "..."},
    {"type": "tiger", "id": "..."}
  ]
}
```

### Tiger Endpoints

#### `POST /api/v1/tigers/identify`
Identify tiger from image.

**Request:** `multipart/form-data`
- `image`: Image file (JPEG, PNG)

**Response:** `200 OK`
```json
{
  "tiger_id": "...",
  "confidence": 0.95,
  "matches": [
    {
      "tiger_id": "...",
      "confidence": 0.95,
      "name": "Tiger Name"
    }
  ]
}
```

#### `GET /api/v1/tigers/{tiger_id}`
Get tiger details.

**Response:** `200 OK`
```json
{
  "tiger_id": "...",
  "name": "Tiger Name",
  "status": "active",
  "images": [...],
  "facilities": [...]
}
```

### Search Endpoints

#### `GET /api/v1/search/global`
Perform global search across all entities.

**Query Parameters:**
- `q`: Search query (required)
- `entity_types` (optional): Comma-separated entity types (investigations,evidence,facilities,tigers)
- `limit` (optional, default: 50): Maximum results per entity type

**Response:** `200 OK`
```json
{
  "query": "tiger",
  "results": {
    "investigations": [...],
    "tigers": [...],
    "facilities": [...],
    "evidence": [...]
  },
  "counts": {
    "investigations": 5,
    "tigers": 10,
    "facilities": 2,
    "evidence": 15
  }
}
```

### Analytics Endpoints

#### `GET /api/v1/analytics/investigations`
Get investigation analytics.

**Query Parameters:**
- `start_date` (optional): Start date filter
- `end_date` (optional): End date filter

**Response:** `200 OK`
```json
{
  "total_investigations": 100,
  "by_status": {...},
  "by_priority": {...},
  "trends": [...]
}
```

#### `GET /api/v1/analytics/evidence`
Get evidence analytics.

#### `GET /api/v1/analytics/verification`
Get verification analytics.

#### `GET /api/v1/analytics/geographic`
Get geographic analytics.

#### `GET /api/v1/analytics/tigers`
Get tiger analytics.

#### `GET /api/v1/analytics/agents`
Get agent performance analytics.

### Export Endpoints

#### `GET /api/v1/investigations/{investigation_id}/export/json`
Export investigation as JSON.

**Query Parameters:**
- `include_evidence` (optional, default: true)
- `include_steps` (optional, default: true)
- `include_metadata` (optional, default: true)

#### `GET /api/v1/investigations/{investigation_id}/export/markdown`
Export investigation as Markdown.

#### `GET /api/v1/investigations/{investigation_id}/export/pdf`
Export investigation as PDF.

#### `GET /api/v1/investigations/{investigation_id}/export/csv`
Export investigation as CSV.

**Query Parameters:**
- `data_type`: Type of data to export (evidence, steps, metadata)

### Notification Endpoints

#### `GET /api/v1/notifications`
Get user notifications.

**Query Parameters:**
- `read` (optional): Filter by read status (true/false)
- `notification_type` (optional): Filter by type
- `priority` (optional): Filter by priority
- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

#### `GET /api/v1/notifications/unread-count`
Get unread notification count.

#### `POST /api/v1/notifications/{notification_id}/read`
Mark notification as read.

#### `POST /api/v1/notifications/read-all`
Mark all notifications as read.

#### `DELETE /api/v1/notifications/{notification_id}`
Delete notification.

### Event Endpoints

#### `GET /api/events/{investigation_id}`
Get investigation events (for event history).

**Query Parameters:**
- `event_type` (optional): Filter by event type
- `limit` (optional, default: 50)

#### `GET /api/events/latest`
Get latest events.

**Query Parameters:**
- `investigation_id` (optional): Filter by investigation
- `event_type` (optional): Filter by event type
- `limit` (optional, default: 20)

#### `GET /api/events/stream`
Server-Sent Events (SSE) stream for real-time updates.

**Query Parameters:**
- `investigation_id` (optional): Filter by investigation

### Audit Endpoints (Admin Only)

#### `GET /api/v1/audit/logs`
Get audit logs (admin only).

**Query Parameters:**
- `user_id` (optional): Filter by user ID
- `action_type` (optional): Filter by action type
- `resource_type` (optional): Filter by resource type
- `status` (optional): Filter by status
- `start_date` (optional): Start date filter
- `end_date` (optional): End date filter
- `limit` (optional, default: 100)
- `offset` (optional, default: 0)

#### `GET /api/v1/audit/summary`
Get audit log summary (admin only).

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Rate Limiting

API requests are limited to **60 requests per minute per IP address**.

Rate limit headers included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time (Unix timestamp)

## Interactive API Documentation

The API includes automatic interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

These interfaces allow you to:
- Browse all available endpoints
- View request/response schemas
- Test endpoints directly from the browser
- Generate client code

