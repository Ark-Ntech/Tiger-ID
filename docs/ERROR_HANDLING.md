# Error Handling Guide

Complete guide to error handling in the Tiger ID backend API.

## Overview

Tiger ID uses a standardized error handling system with:
- Custom exception classes for common error scenarios
- Automatic conversion to JSON responses
- Consistent error format across all endpoints
- Secure error messages that don't expose internal details

## Quick Start

### Using Standard Exceptions

```python
from backend.api.error_handlers import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    BadRequestError,
)

# In your route handler
@router.get("/tigers/{tiger_id}")
def get_tiger(tiger_id: str):
    tiger = db.query(Tiger).filter(Tiger.id == tiger_id).first()

    if not tiger:
        raise NotFoundError("Tiger", tiger_id)

    return tiger
```

### Response Format

All errors return this JSON format:

```json
{
    "error": "Human-readable error message",
    "code": "MACHINE_READABLE_ERROR_CODE",
    "status": 404
}
```

## Exception Classes

### Base Class: APIError

All exceptions inherit from `APIError`:

```python
from backend.api.error_handlers import APIError

# Create custom error
raise APIError(
    status_code=400,
    detail="Something went wrong",
    error_code="CUSTOM_ERROR",
    headers={"X-Custom-Header": "value"}  # Optional
)
```

### NotFoundError (404)

Use when a requested resource doesn't exist:

```python
from backend.api.error_handlers import NotFoundError

raise NotFoundError("Tiger", "TIG-001")
# Returns: {"error": "Tiger 'TIG-001' not found", "code": "NOT_FOUND", "status": 404}

raise NotFoundError("Investigation", investigation_id)
raise NotFoundError("Facility", facility_id)
raise NotFoundError("User", username)
```

### ValidationError (422)

Use when request data fails validation:

```python
from backend.api.error_handlers import ValidationError

raise ValidationError("Image must be at least 224x224 pixels")
# Returns: {"error": "Image must be at least 224x224 pixels", "code": "VALIDATION_ERROR", "status": 422}

raise ValidationError("Invalid date format. Use YYYY-MM-DD")
raise ValidationError("Name is required and must be at least 3 characters")
```

### AuthenticationError (401)

Use when authentication is required but not provided or invalid:

```python
from backend.api.error_handlers import AuthenticationError

raise AuthenticationError()  # Default message
# Returns: {"error": "Not authenticated", "code": "AUTHENTICATION_ERROR", "status": 401}

raise AuthenticationError("Token has expired")
raise AuthenticationError("Invalid API key")
raise AuthenticationError("Session expired. Please log in again")
```

### AuthorizationError (403)

Use when user is authenticated but lacks permission:

```python
from backend.api.error_handlers import AuthorizationError

raise AuthorizationError()  # Default message
# Returns: {"error": "Not authorized", "code": "AUTHORIZATION_ERROR", "status": 403}

raise AuthorizationError("Admin role required to delete tigers")
raise AuthorizationError("You can only edit your own investigations")
```

### ConflictError (409)

Use when request conflicts with current resource state:

```python
from backend.api.error_handlers import ConflictError

raise ConflictError("Tiger with this ID already exists")
# Returns: {"error": "Tiger with this ID already exists", "code": "CONFLICT", "status": 409}

raise ConflictError("Investigation is already running")
raise ConflictError("Cannot delete facility with active tigers")
```

### RateLimitError (429)

Use when client exceeds rate limits:

```python
from backend.api.error_handlers import RateLimitError

raise RateLimitError()  # Default message
# Returns: {"error": "Rate limit exceeded", "code": "RATE_LIMIT_EXCEEDED", "status": 429}

raise RateLimitError("Too many requests. Try again in 60 seconds.", retry_after=60)
# Includes header: Retry-After: 60
```

### ServiceUnavailableError (503)

Use when a dependent service is unavailable:

```python
from backend.api.error_handlers import ServiceUnavailableError

raise ServiceUnavailableError()  # Default message
# Returns: {"error": "Service temporarily unavailable", "code": "SERVICE_UNAVAILABLE", "status": 503}

raise ServiceUnavailableError("Modal GPU service is currently unavailable")
raise ServiceUnavailableError("Database maintenance in progress")
```

### BadRequestError (400)

Use for general bad request errors:

```python
from backend.api.error_handlers import BadRequestError

raise BadRequestError("Missing required file upload")
# Returns: {"error": "Missing required file upload", "code": "BAD_REQUEST", "status": 400}

raise BadRequestError("Invalid image format. Only JPEG and PNG supported")
raise BadRequestError("Request body is empty")
```

## Usage Patterns

### In Route Handlers

```python
from fastapi import APIRouter, Depends
from backend.api.error_handlers import NotFoundError, ValidationError
from backend.database import get_db

router = APIRouter()

@router.post("/tigers")
def create_tiger(tiger_data: dict, db: Session = Depends(get_db)):
    # Validation
    if not tiger_data.get("name"):
        raise ValidationError("Tiger name is required")

    # Check for conflicts
    existing = db.query(Tiger).filter(Tiger.name == tiger_data["name"]).first()
    if existing:
        raise ConflictError(f"Tiger with name '{tiger_data['name']}' already exists")

    # Create tiger
    tiger = Tiger(**tiger_data)
    db.add(tiger)
    db.commit()

    return {"tiger_id": tiger.id}

@router.get("/tigers/{tiger_id}")
def get_tiger(tiger_id: str, db: Session = Depends(get_db)):
    tiger = db.query(Tiger).filter(Tiger.id == tiger_id).first()

    if not tiger:
        raise NotFoundError("Tiger", tiger_id)

    return tiger
```

### In Service Layer

```python
class TigerService:
    def __init__(self, db: Session):
        self.db = db

    def get_tiger(self, tiger_id: str) -> Tiger:
        """Get tiger by ID or raise NotFoundError."""
        tiger = self.db.query(Tiger).filter(Tiger.id == tiger_id).first()

        if not tiger:
            raise NotFoundError("Tiger", tiger_id)

        return tiger

    def update_tiger(self, tiger_id: str, data: dict) -> Tiger:
        """Update tiger or raise appropriate error."""
        tiger = self.get_tiger(tiger_id)  # Raises NotFoundError if not found

        # Validation
        if "name" in data and len(data["name"]) < 3:
            raise ValidationError("Tiger name must be at least 3 characters")

        # Update
        for key, value in data.items():
            setattr(tiger, key, value)

        self.db.commit()
        return tiger
```

### With Authentication

```python
from backend.auth.auth import get_current_user
from backend.api.error_handlers import AuthorizationError

@router.delete("/tigers/{tiger_id}")
def delete_tiger(
    tiger_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check permissions
    if current_user.role != "admin":
        raise AuthorizationError("Admin role required to delete tigers")

    tiger = db.query(Tiger).filter(Tiger.id == tiger_id).first()
    if not tiger:
        raise NotFoundError("Tiger", tiger_id)

    db.delete(tiger)
    db.commit()

    return {"message": "Tiger deleted successfully"}
```

### With External Services

```python
from backend.api.error_handlers import ServiceUnavailableError

async def call_modal_service(image_data: bytes):
    try:
        response = await modal_client.identify(image_data)
        return response
    except Exception as e:
        logger.error(f"Modal service error: {e}")
        raise ServiceUnavailableError("ML identification service is currently unavailable")
```

## Best Practices

### 1. Use Specific Exception Classes

❌ **Bad:**
```python
raise APIError(404, "Not found", "NOT_FOUND")
```

✅ **Good:**
```python
raise NotFoundError("Tiger", tiger_id)
```

### 2. Provide Context in Error Messages

❌ **Bad:**
```python
raise ValidationError("Invalid input")
```

✅ **Good:**
```python
raise ValidationError("Image dimensions must be at least 224x224 pixels (received 100x100)")
```

### 3. Don't Expose Sensitive Information

❌ **Bad:**
```python
raise APIError(500, f"Database error: {str(db_exception)}")  # May expose connection strings
```

✅ **Good:**
```python
logger.exception(f"Database error: {db_exception}")  # Log full details
raise ServiceUnavailableError("Database temporarily unavailable")  # Generic message to user
```

### 4. Use Appropriate Status Codes

- **404 (NotFoundError)**: Resource doesn't exist
- **400 (BadRequestError)**: Malformed request
- **422 (ValidationError)**: Valid request format, but invalid data
- **401 (AuthenticationError)**: Not authenticated
- **403 (AuthorizationError)**: Authenticated but not authorized
- **409 (ConflictError)**: Resource conflict (duplicate, state conflict)
- **429 (RateLimitError)**: Too many requests
- **503 (ServiceUnavailableError)**: Dependent service unavailable
- **500 (Generic)**: Unexpected server error (handled automatically)

### 5. Let Unexpected Exceptions Bubble Up

❌ **Bad:**
```python
try:
    result = some_operation()
except Exception as e:
    raise APIError(500, str(e))  # Exposes internal details
```

✅ **Good:**
```python
# Let unexpected exceptions bubble up
# They'll be caught by generic_exception_handler
result = some_operation()
```

The generic exception handler will:
- Log the full exception with traceback
- Return a safe generic error message
- Not expose internal details

## Testing Error Handling

### Test Exception Raising

```python
import pytest
from backend.api.error_handlers import NotFoundError

def test_service_raises_not_found():
    service = TigerService(db)

    with pytest.raises(NotFoundError) as exc_info:
        service.get_tiger("nonexistent-id")

    assert exc_info.value.status_code == 404
    assert "nonexistent-id" in exc_info.value.detail
```

### Test Error Responses

```python
def test_get_nonexistent_tiger_returns_404(test_client):
    response = test_client.get("/api/v1/tigers/fake-id")

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "NOT_FOUND"
    assert "error" in data
```

### Test Error Format

```python
def test_error_response_format(test_client):
    response = test_client.get("/api/v1/tigers/fake-id")

    data = response.json()
    assert "error" in data  # Human-readable message
    assert "code" in data   # Machine-readable code
    assert "status" in data # HTTP status code
```

## Error Handling Architecture

### Exception Flow

```
Route Handler
    ↓
Raises APIError or subclass
    ↓
FastAPI catches exception
    ↓
api_error_handler() called
    ↓
Logs warning with details
    ↓
Returns JSONResponse with standard format
```

### Generic Exception Flow

```
Route Handler
    ↓
Raises unexpected exception (ValueError, etc.)
    ↓
FastAPI catches exception
    ↓
generic_exception_handler() called
    ↓
Logs full exception with traceback
    ↓
Returns safe generic error (no internal details)
```

### Registration

Handlers are registered in `backend/api/app.py`:

```python
from backend.api.error_handlers import (
    APIError,
    api_error_handler,
    generic_exception_handler,
)

app = FastAPI()

# Register exception handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

## Frontend Integration

### TypeScript Types

```typescript
interface ErrorResponse {
  error: string;   // Human-readable message
  code: string;    // Machine-readable error code
  status: number;  // HTTP status code
}
```

### Handling Errors

```typescript
async function getTiger(tigerId: string): Promise<Tiger> {
  try {
    const response = await fetch(`/api/v1/tigers/${tigerId}`);

    if (!response.ok) {
      const error: ErrorResponse = await response.json();

      // Handle specific error codes
      switch (error.code) {
        case 'NOT_FOUND':
          showNotification('Tiger not found', 'error');
          break;
        case 'AUTHENTICATION_ERROR':
          redirectToLogin();
          break;
        case 'AUTHORIZATION_ERROR':
          showNotification('You do not have permission', 'error');
          break;
        default:
          showNotification(error.error, 'error');
      }

      throw error;
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to get tiger:', error);
    throw error;
  }
}
```

## Logging

### Error Logging

```python
import logging
logger = logging.getLogger(__name__)

# APIError exceptions log a warning
# (logged by api_error_handler)
logger.warning(f"API error: {exc.error_code} - {exc.detail}")

# Unexpected exceptions log with full traceback
# (logged by generic_exception_handler)
logger.exception(f"Unexpected error: {exc}")
```

### Production Logging

In production, integrate with:
- **Sentry**: Automatic error tracking and alerting
- **CloudWatch/Datadog**: Log aggregation and monitoring
- **Custom dashboards**: Track error rates by code/endpoint

## Related Files

- **Implementation**: `C:\Users\noah\Desktop\Tiger ID\backend\api\error_handlers.py`
- **Tests**: `C:\Users\noah\Desktop\Tiger ID\tests\test_api\test_error_handlers.py`
- **Registration**: `C:\Users\noah\Desktop\Tiger ID\backend\api\app.py`
- **Legacy exceptions**: `C:\Users\noah\Desktop\Tiger ID\backend\core\exceptions.py` (being phased out)

## Migration from Legacy Exceptions

If you encounter code using old `TigerIDException`:

```python
# Old (backend/core/exceptions.py)
from backend.core.exceptions import TigerNotFoundError
raise TigerNotFoundError("TIG-001")

# New (backend/api/error_handlers.py)
from backend.api.error_handlers import NotFoundError
raise NotFoundError("Tiger", "TIG-001")
```

## FAQ

### When should I create a custom exception vs using APIError?

Use custom exceptions for common, reusable error scenarios. Use `APIError` directly for one-off errors.

### Should I catch exceptions and re-raise as APIError?

Only catch exceptions you expect and can handle. Let unexpected exceptions bubble up to the generic handler.

### How do I add custom data to error responses?

Currently, error responses only include `error`, `code`, and `status`. For additional data, consider using a custom response format or extending the `APIError` class.

### Can I override the error format for specific routes?

Yes, but it's not recommended for consistency. If needed, catch the exception in your route and return a custom response.

### How do I handle validation errors from Pydantic?

FastAPI automatically handles Pydantic validation errors. For custom validation, use `ValidationError`:

```python
from pydantic import BaseModel
from backend.api.error_handlers import ValidationError

class TigerCreate(BaseModel):
    name: str
    age: int

def validate_tiger_age(age: int):
    if age < 0 or age > 30:
        raise ValidationError("Tiger age must be between 0 and 30")
```
