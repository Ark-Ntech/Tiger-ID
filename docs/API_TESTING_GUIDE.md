# API Testing Guide

This document provides a guide for testing all API endpoints in the Tiger ID application.

## Prerequisites

1. Backend server running on `http://localhost:8000`
2. Frontend server running on `http://localhost:5173`
3. Authentication token (obtain via login)

## Getting Authentication Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

Save the token from the response for use in subsequent requests.

## Core Endpoints

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "models": {...}
}
```

### 2. Global Search

```bash
curl -X POST http://localhost:8000/api/v1/search/global \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "alabama", "limit": 10}'
```

### 3. MCP Tools

```bash
curl http://localhost:8000/api/v1/investigations/mcp-tools \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected:** List of available MCP tools organized by server

### 4. Available Models

```bash
curl http://localhost:8000/api/v1/models/available \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected:** List of available RE-ID models

### 5. Model Testing

```bash
curl -X POST http://localhost:8000/api/v1/models/test \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "images=@path/to/image.jpg" \
  -F "model_name=tiger_reid"
```

### 6. Tiger Identification

```bash
curl -X POST http://localhost:8000/api/v1/tigers/identify \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@path/to/tiger_image.jpg" \
  -F "model_name=tiger_reid" \
  -F "similarity_threshold=0.8"
```

### 7. Facilities Import

```bash
curl -X POST http://localhost:8000/api/v1/facilities/import-excel \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/facilities.xlsx" \
  -F "update_existing=true"
```

### 8. Dashboard Stats

```bash
curl http://localhost:8000/api/v1/dashboard/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 9. Templates

**Get Templates:**
```bash
curl http://localhost:8000/api/v1/templates \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Create Template:**
```bash
curl -X POST http://localhost:8000/api/v1/templates \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Standard Investigation",
    "description": "Standard investigation workflow",
    "workflow_steps": [],
    "default_agents": []
  }'
```

**Apply Template:**
```bash
curl -X POST "http://localhost:8000/api/v1/templates/{template_id}/apply?investigation_id={investigation_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 10. Investigation Tools

**Web Search:**
```bash
curl -X POST http://localhost:8000/api/v1/investigations/web-search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tiger facility",
    "limit": 10
  }'
```

**Reverse Image Search:**
```bash
curl -X POST http://localhost:8000/api/v1/investigations/reverse-image-search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@path/to/image.jpg"
```

**News Search:**
```bash
curl -X POST http://localhost:8000/api/v1/investigations/news-search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tiger trafficking",
    "limit": 10
  }'
```

## Analytics Endpoints

### Investigation Analytics
```bash
curl http://localhost:8000/api/v1/analytics/investigations \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Evidence Analytics
```bash
curl http://localhost:8000/api/v1/analytics/evidence \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Geographic Analytics
```bash
curl http://localhost:8000/api/v1/analytics/geographic \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Tiger Analytics
```bash
curl http://localhost:8000/api/v1/analytics/tigers \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Testing Checklist

- [ ] Health check returns healthy status
- [ ] Global search returns results
- [ ] MCP tools list loads without errors
- [ ] Models are available and listed
- [ ] Model testing works with test images
- [ ] Tiger identification works
- [ ] Facilities import works with Excel file
- [ ] Dashboard stats load correctly
- [ ] Templates can be created and applied
- [ ] Investigation tools work (web search, image search, etc.)
- [ ] Analytics endpoints return data
- [ ] File uploads work correctly
- [ ] Authentication works
- [ ] Error handling works (test with invalid requests)

## Common Issues

### 401 Unauthorized
- Token expired or invalid
- Solution: Re-login and get new token

### 500 Internal Server Error
- Check backend logs
- Verify database connection
- Check model files exist

### 404 Not Found
- Verify endpoint URL is correct
- Check router is registered in `app.py`

### File Upload Errors
- Verify file size limits
- Check file format is supported
- Verify multipart/form-data encoding

## Automated Testing

For automated testing, consider:
1. **pytest** - Python testing framework
2. **Postman** - API testing tool
3. **Newman** - Postman CLI for CI/CD
4. **Jest** - Frontend testing (for API client)

## Performance Testing

Test API performance:
```bash
# Using Apache Bench
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/dashboard/stats
```

Monitor:
- Response times
- Error rates
- Throughput
- Resource usage

