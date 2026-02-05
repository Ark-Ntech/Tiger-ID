# Modal Client Tests

Comprehensive test suite for Modal client infrastructure, covering the `BaseModalClient` base class and all client implementations.

## Test Structure

### Core Test Files

| File | Coverage |
|------|----------|
| `test_modal_clients.py` | Base class, inheritance, singletons, basic functionality |
| `test_modal_clients_advanced.py` | Concurrency, timeouts, image formats, error recovery |
| `test_modal_clients_implementations.py` | Implementation-specific tests, cross-client consistency |
| `conftest.py` | Shared fixtures and pytest configuration |

## Test Categories

### 1. BaseModalClient Tests (`test_modal_clients.py`)

- **Initialization**: Default and custom parameters, mock mode configuration
- **Retry Logic**: Exponential backoff, failure handling, timeout behavior
- **Statistics Tracking**: Request counters, success/failure tracking
- **Modal Function Loading**: Lazy loading, caching, connection errors
- **Error Handling**: ModalClientError, ModalUnavailableError

### 2. Client Inheritance Tests

- Verify all clients inherit from `BaseModalClient`
- Test singleton pattern for all clients
- Validate property implementations (app_name, class_name, EMBEDDING_DIM)

### 3. Advanced Tests (`test_modal_clients_advanced.py`)

- **Concurrency**: Parallel requests, thread safety
- **Timeouts**: Custom timeouts, timeout recovery
- **Image Formats**: RGB, RGBA, grayscale, various sizes
- **Error Recovery**: Fallback to mock, graceful degradation

### 4. Implementation Tests (`test_modal_clients_implementations.py`)

- **WildlifeToolsClient**: 1536-dim embeddings, JPEG conversion
- **CVWC2019Client**: 2048-dim embeddings, ResNet152
- **TransReIDClient**: 768-dim embeddings, ViT-Base
- **MegaDescriptorBClient**: 1024-dim embeddings, Swin-Base
- **MatchAnythingClient**: Keypoint matching, health checks

## Running Tests

### Run All Tests
```bash
pytest tests/test_infrastructure/
```

### Run Specific Test File
```bash
pytest tests/test_infrastructure/test_modal_clients.py
```

### Run Tests with Coverage
```bash
pytest tests/test_infrastructure/ --cov=backend.infrastructure.modal --cov-report=html
```

### Run Tests by Category
```bash
# Run only base class tests
pytest tests/test_infrastructure/test_modal_clients.py::TestBaseModalClient

# Run only concurrency tests
pytest tests/test_infrastructure/test_modal_clients_advanced.py::TestConcurrency

# Run only implementation tests
pytest tests/test_infrastructure/test_modal_clients_implementations.py
```

### Skip Slow Tests
```bash
pytest tests/test_infrastructure/ -m "not slow"
```

## Test Fixtures

### Image Fixtures
- `sample_rgb_image`: 100x100 RGB image
- `sample_image_pair`: Two images for matching tests
- `sample_large_image`: 1000x1000 image for performance tests
- `sample_grayscale_image`: Grayscale image for format tests
- `sample_rgba_image`: RGBA image with transparency

### Mock Response Fixtures
- `mock_modal_response`: Factory for creating mock embedding responses
- `mock_match_response`: Factory for creating mock matching responses

### Utility Fixtures
- `reset_singletons`: Auto-runs to reset singleton state between tests

## Key Test Scenarios

### Retry Logic
```python
@pytest.mark.asyncio
async def test_call_with_retry_exponential_backoff():
    # Tests that retry delay doubles: 0.1, 0.2, 0.4, ...
```

### Concurrent Requests
```python
@pytest.mark.asyncio
async def test_concurrent_requests_same_client():
    # Tests 10 concurrent requests to verify thread safety
```

### Mock Fallback
```python
@pytest.mark.asyncio
async def test_fallback_on_modal_error():
    # Tests graceful fallback to mock when Modal fails
```

### Image Format Handling
```python
@pytest.mark.asyncio
async def test_rgba_image_conversion():
    # Tests RGBA to RGB conversion before processing
```

## Coverage Goals

- **BaseModalClient**: 100% line coverage
- **Client Implementations**: 95%+ line coverage
- **Error Paths**: All exception handlers tested
- **Mock Provider**: Full integration coverage

## Continuous Integration

Tests run automatically on:
- Pull requests to main branch
- Push to main branch
- Nightly builds (full suite including slow tests)

## Common Issues

### Singleton State Leakage
If tests fail intermittently, ensure `reset_singletons` fixture is working:
```python
def test_something(reset_singletons):
    # This ensures clean state
    client = get_wildlife_tools_client()
```

### Async Test Warnings
All async tests must use `@pytest.mark.asyncio`:
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_call()
```

### Mock Mode Not Enabled
Some tests require mock mode. Use fixtures:
```python
def test_with_mock():
    client = WildlifeToolsClient(use_mock=True)
    # Test proceeds without real Modal connection
```

## Adding New Tests

### For New Client Implementation

1. Add tests in `test_modal_clients_implementations.py`
2. Test basic properties (app_name, class_name, EMBEDDING_DIM)
3. Test generate_embedding in mock and production modes
4. Test fallback behavior
5. Add to cross-client consistency tests

### For New BaseModalClient Feature

1. Add tests in `test_modal_clients.py`
2. Create concrete test class inheriting from BaseModalClient
3. Test with mocked Modal functions
4. Add edge case tests in `test_modal_clients_advanced.py`

## Metrics

Current test coverage:
- Total tests: 100+
- BaseModalClient coverage: 100%
- Client implementations: 95%+
- Average test execution time: < 5 seconds

## References

- BaseModalClient: `backend/infrastructure/modal/base_client.py`
- Client implementations: `backend/infrastructure/modal/clients/*.py`
- Mock provider: `backend/infrastructure/modal/mock_provider.py`
