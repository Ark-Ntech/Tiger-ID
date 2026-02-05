# Error Handling Quick Reference

## Import
```python
from backend.api.error_handlers import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    RateLimitError,
    ServiceUnavailableError,
    BadRequestError,
    APIError,  # For custom errors
)
```

## Quick Reference Table

| Exception | Status | Error Code | Use When |
|-----------|--------|------------|----------|
| `NotFoundError("Resource", "id")` | 404 | NOT_FOUND | Resource doesn't exist |
| `ValidationError("message")` | 422 | VALIDATION_ERROR | Invalid input data |
| `AuthenticationError("message")` | 401 | AUTHENTICATION_ERROR | Not authenticated |
| `AuthorizationError("message")` | 403 | AUTHORIZATION_ERROR | No permission |
| `ConflictError("message")` | 409 | CONFLICT | Resource conflict |
| `RateLimitError("msg", retry_after=60)` | 429 | RATE_LIMIT_EXCEEDED | Rate limit hit |
| `ServiceUnavailableError("message")` | 503 | SERVICE_UNAVAILABLE | Service down |
| `BadRequestError("message")` | 400 | BAD_REQUEST | Malformed request |

## Common Patterns

### Resource Not Found
```python
tiger = db.query(Tiger).filter(Tiger.id == tiger_id).first()
if not tiger:
    raise NotFoundError("Tiger", tiger_id)
```

### Input Validation
```python
if len(name) < 3:
    raise ValidationError("Name must be at least 3 characters")
```

### Authentication Check
```python
if not token or token_expired:
    raise AuthenticationError("Token has expired")
```

### Permission Check
```python
if current_user.role != "admin":
    raise AuthorizationError("Admin role required")
```

### Duplicate Check
```python
if db.query(Tiger).filter(Tiger.name == name).first():
    raise ConflictError(f"Tiger with name '{name}' already exists")
```

### Rate Limiting
```python
if requests_count > limit:
    raise RateLimitError("Too many requests", retry_after=60)
```

### External Service Error
```python
try:
    response = await modal_service.call()
except Exception:
    raise ServiceUnavailableError("ML service unavailable")
```

### Bad Request
```python
if not request.files:
    raise BadRequestError("File upload required")
```

## Response Format

All errors return:
```json
{
    "error": "Human-readable message",
    "code": "MACHINE_READABLE_CODE",
    "status": 404
}
```

## Testing

```python
def test_not_found_error(test_client):
    response = test_client.get("/api/v1/tigers/fake-id")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
```

## Best Practices

✅ **DO**: Use specific exception classes
```python
raise NotFoundError("Tiger", tiger_id)
```

❌ **DON'T**: Use generic APIError
```python
raise APIError(404, "Not found", "NOT_FOUND")
```

✅ **DO**: Provide helpful error messages
```python
raise ValidationError("Image must be at least 224x224 pixels (received 100x100)")
```

❌ **DON'T**: Use vague messages
```python
raise ValidationError("Invalid input")
```

✅ **DO**: Let unexpected errors bubble up
```python
result = some_operation()  # Let it fail naturally
```

❌ **DON'T**: Catch and expose internals
```python
try:
    result = some_operation()
except Exception as e:
    raise APIError(500, str(e))  # Exposes internals!
```

## HTTP Status Code Guide

- **400**: Malformed request (BadRequestError)
- **401**: Not authenticated (AuthenticationError)
- **403**: Not authorized (AuthorizationError)
- **404**: Resource not found (NotFoundError)
- **409**: Resource conflict (ConflictError)
- **422**: Invalid data (ValidationError)
- **429**: Rate limited (RateLimitError)
- **500**: Server error (Generic handler)
- **503**: Service unavailable (ServiceUnavailableError)

## Frontend Error Handling

```typescript
try {
  const response = await fetch('/api/v1/tigers/123');
  if (!response.ok) {
    const error = await response.json();
    switch (error.code) {
      case 'NOT_FOUND':
        showNotification('Tiger not found');
        break;
      case 'AUTHENTICATION_ERROR':
        redirectToLogin();
        break;
      default:
        showNotification(error.error);
    }
  }
} catch (error) {
  console.error(error);
}
```
