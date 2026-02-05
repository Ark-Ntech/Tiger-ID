# Error Handler Tests

Comprehensive test suite for the Tiger ID error handling middleware and standardized exceptions.

## Overview

This test suite validates the error handling system including:
- Custom exception classes
- Exception handlers
- Integration with FastAPI routes
- Error response format consistency

## Test Coverage

### 1. Exception Classes (27 tests)

#### `TestAPIError` (3 tests)
- Basic initialization with all parameters
- Initialization with custom headers
- Initialization without error code

#### `TestNotFoundError` (3 tests)
- Basic initialization with resource and identifier
- UUID identifier handling
- Different resource types

#### `TestValidationError` (3 tests)
- Basic initialization
- Detailed validation messages
- Multiple field errors

#### `TestAuthenticationError` (3 tests)
- Default message
- Custom message
- Invalid credentials scenario

#### `TestAuthorizationError` (3 tests)
- Default message
- Custom message
- Permission denial scenario

#### `TestConflictError` (3 tests)
- Basic initialization
- Duplicate resource conflicts
- State conflicts

#### `TestRateLimitError` (3 tests)
- Default message
- With Retry-After header
- Custom message with retry timing

#### `TestServiceUnavailableError` (3 tests)
- Default message
- Custom service-specific message
- Maintenance scenario

#### `TestBadRequestError` (3 tests)
- Basic initialization
- Invalid format scenario
- Missing field scenario

### 2. Exception Handlers (10 tests)

#### `TestAPIErrorHandler` (6 tests)
- Basic error handling
- Handling with custom headers
- NotFoundError handling
- ValidationError handling
- AuthenticationError handling
- Logging verification

#### `TestGenericExceptionHandler` (4 tests)
- Generic unexpected exception handling
- Security: hiding internal details
- Exception logging
- Different exception types

### 3. Route Integration (4 tests)

#### `TestErrorHandlerIntegration`
- Routes returning NotFoundError
- Routes returning ValidationError
- Routes returning AuthenticationError
- Consistent error format across routes

### 4. Response Format (3 tests)

#### `TestErrorResponseFormat`
- Required fields presence
- Response without error code
- JSON serialization

### 5. Inheritance (2 tests)

#### `TestErrorInheritance`
- All custom errors inherit from APIError
- Error handler catches all subclasses

## Running Tests

### Run all error handler tests
```bash
cd "C:\Users\noah\Desktop\Tiger ID"
python -m pytest tests/test_api/test_error_handlers.py -v
```

### Run specific test class
```bash
python -m pytest tests/test_api/test_error_handlers.py::TestAPIError -v
```

### Run with output
```bash
python -m pytest tests/test_api/test_error_handlers.py -v -s
```

### Run with short traceback
```bash
python -m pytest tests/test_api/test_error_handlers.py -v --tb=short
```

## Test Results

All 46 tests pass successfully:
- ✅ 27 exception class tests
- ✅ 10 exception handler tests
- ✅ 4 route integration tests
- ✅ 3 response format tests
- ✅ 2 inheritance tests

## Error Response Format

All errors follow this standardized format:

```json
{
    "error": "Human-readable error message",
    "code": "MACHINE_READABLE_ERROR_CODE",
    "status": 404
}
```

### HTTP Status Codes

| Exception | Status Code | Error Code |
|-----------|-------------|------------|
| NotFoundError | 404 | NOT_FOUND |
| ValidationError | 422 | VALIDATION_ERROR |
| AuthenticationError | 401 | AUTHENTICATION_ERROR |
| AuthorizationError | 403 | AUTHORIZATION_ERROR |
| ConflictError | 409 | CONFLICT |
| RateLimitError | 429 | RATE_LIMIT_EXCEEDED |
| ServiceUnavailableError | 503 | SERVICE_UNAVAILABLE |
| BadRequestError | 400 | BAD_REQUEST |
| Generic Exception | 500 | INTERNAL_ERROR |

## Key Features Tested

### 1. Exception Class Features
- Status code assignment
- Error message formatting
- Error code generation
- Custom headers (e.g., Retry-After)
- Resource-specific error details

### 2. Handler Features
- JSONResponse generation
- Proper status code mapping
- Header propagation
- Logging (warnings for API errors, exception logs for unexpected errors)
- Security: Generic errors don't expose internal details

### 3. Integration Features
- FastAPI exception handler registration
- Route-level error handling
- Authentication/authorization error handling
- Consistent error format across all endpoints

### 4. Security Features
- Generic exception handler hides sensitive details
- No password or credential exposure in error messages
- Safe error messages for production

## Testing Strategy

### Unit Tests
Tests for individual exception classes verify:
- Correct initialization
- Proper attribute assignment
- Inheritance hierarchy
- Error message formatting

### Handler Tests
Tests for exception handlers verify:
- Correct JSON response generation
- Status code mapping
- Header propagation
- Logging behavior

### Integration Tests
Tests with FastAPI client verify:
- End-to-end error handling
- Route-level behavior
- Authentication/authorization flows
- Response format consistency

## Dependencies

- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `unittest.mock` - Mocking support
- FastAPI `TestClient` - HTTP testing

## Notes

### Authentication in Tests
Some integration tests use `authenticated_client` fixture to test protected endpoints. Tests gracefully skip if routes require specific permissions.

### Flexible Assertions
Integration tests are designed to be flexible:
- Accept multiple valid status codes where appropriate
- Skip tests when authentication requirements aren't met
- Verify error structure even if exact format varies slightly

### Bcrypt Import Issue
Coverage reports may fail due to a known pytest-cov issue with bcrypt native extensions. Tests run successfully without coverage reporting.

## Future Enhancements

Potential additions to the test suite:
1. Performance tests for error handling overhead
2. Stress tests with many concurrent errors
3. Tests for error handling in websocket connections
4. Tests for error handling in background tasks
5. Integration tests with actual database errors
6. Tests for custom error serialization formats (XML, etc.)
