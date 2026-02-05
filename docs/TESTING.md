# Testing Guide

This document describes how to run and write tests for the Tiger ID system.

---

## Table of Contents

- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [CI/CD Integration](#cicd-integration)

---

## Backend Testing

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_modal_integration.py

# Run specific test
pytest tests/test_modal_integration.py::test_tiger_reid_embedding -v

# Run with coverage
pytest --cov=backend --cov-report=html

# Run tests matching pattern
pytest -k "modal" -v
```

### Test Categories

| Category | Location | Description |
|----------|----------|-------------|
| Unit tests | `tests/test_*.py` | Individual function/class tests |
| Modal integration | `tests/test_modal_integration.py` | Modal GPU inference tests |
| API tests | `tests/test_api_*.py` | FastAPI endpoint tests |
| Service tests | `tests/test_services_*.py` | Business logic tests |

### Modal Integration Tests

The Modal integration test suite validates all model deployments:

```bash
# Run Modal tests only
pytest tests/test_modal_integration.py -v

# Test specific model
pytest tests/test_modal_integration.py -k "wildlife_tools" -v
```

**Test coverage includes:**
- ModalClient initialization
- Tiger ReID embedding generation
- MegaDetector animal detection
- All ensemble model embeddings
- Retry logic and exponential backoff
- Request queueing
- Error handling and fallback

### Writing Backend Tests

```python
import pytest
from backend.services.tiger import IdentificationService

@pytest.fixture
def identification_service():
    return IdentificationService()

@pytest.mark.asyncio
async def test_identify_tiger(identification_service):
    """Test tiger identification returns expected structure."""
    result = await identification_service.identify(
        image_path="tests/fixtures/tiger.jpg"
    )

    assert result is not None
    assert "matches" in result
    assert "confidence" in result
```

### Test Fixtures

Place test fixtures in `tests/fixtures/`:
- Sample tiger images
- Mock API responses
- Database seed data

---

## Frontend Testing

### Running Tests

```bash
cd frontend

# Run unit tests with Vitest
npm run test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm run test -- Investigation2.test.tsx
```

### Test Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── __tests__/     # Component tests
│   ├── hooks/
│   │   └── __tests__/     # Hook tests
│   └── utils/
│       └── __tests__/     # Utility tests
└── tests/
    └── setup.ts           # Test configuration
```

### Writing Component Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Investigation2ResultsEnhanced } from '../Investigation2ResultsEnhanced';

describe('Investigation2ResultsEnhanced', () => {
  it('displays match results', () => {
    const mockResults = {
      matches: [{ tiger_id: 'T-001', confidence: 0.87 }],
    };

    render(<Investigation2ResultsEnhanced results={mockResults} />);

    expect(screen.getByText('T-001')).toBeInTheDocument();
    expect(screen.getByText('87%')).toBeInTheDocument();
  });
});
```

### TypeScript Type Checking

```bash
# Run type checking (no emit)
npx tsc --noEmit

# Watch mode
npx tsc --noEmit --watch
```

---

## Integration Testing

### API Integration Tests

Test API endpoints with a running backend:

```bash
# Start backend
cd backend && uvicorn main:app --reload

# Run integration tests
pytest tests/integration/ -v
```

### Database Integration

```python
import pytest
from sqlalchemy import create_engine
from backend.database.models import Base

@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
```

---

## End-to-End Testing

### Playwright Setup

```bash
cd frontend

# Install Playwright
npx playwright install

# Run E2E tests
npm run test:e2e

# Run in headed mode (visible browser)
npm run test:e2e -- --headed

# Run specific test
npm run test:e2e -- investigation.spec.ts
```

### E2E Test Structure

```
frontend/
└── e2e/
    ├── investigation.spec.ts
    ├── auth.spec.ts
    └── tiger-search.spec.ts
```

### Writing E2E Tests

```typescript
import { test, expect } from '@playwright/test';

test.describe('Investigation Workflow', () => {
  test('complete investigation flow', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');

    // Navigate to Investigation 2.0
    await page.click('text=Investigations');
    await page.click('text=New Investigation');

    // Upload image
    await page.setInputFiles('input[type="file"]', 'e2e/fixtures/tiger.jpg');

    // Wait for results
    await expect(page.locator('.results-panel')).toBeVisible({ timeout: 60000 });

    // Verify results displayed
    await expect(page.locator('.match-card')).toHaveCount(5);
  });
});
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest --cov=backend

      - name: Type check
        run: mypy backend/

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Type check
        run: cd frontend && npx tsc --noEmit

      - name: Run tests
        run: cd frontend && npm run test

      - name: Run E2E tests
        run: cd frontend && npx playwright install && npm run test:e2e
```

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: backend-tests
        name: Backend Tests
        entry: pytest tests/ -x --tb=short
        language: system
        pass_filenames: false

      - id: frontend-typecheck
        name: Frontend TypeCheck
        entry: bash -c 'cd frontend && npx tsc --noEmit'
        language: system
        pass_filenames: false
```

---

## Test Environment Variables

Create `tests/.env.test`:

```env
DATABASE_URL=sqlite:///:memory:
MODAL_ENABLED=false
SECRET_KEY=test-secret
JWT_SECRET_KEY=test-jwt-secret
```

---

## Related Documentation

- [Development Guide](./DEPLOYMENT.md) - Local development setup
- [Modal Infrastructure](./MODAL.md) - GPU testing configuration
- [Architecture](./ARCHITECTURE.md) - System components to test

---

*Last Updated: February 2026*
