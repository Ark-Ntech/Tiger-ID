# Contributing to Tiger ID

Thank you for your interest in contributing to the Tiger Trafficking Investigation System! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/tiger-investigation.git
   cd tiger-investigation
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```
6. **Set up database**:
   ```bash
   docker-compose up -d postgres redis
   alembic upgrade head
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes

### 2. Make Your Changes

- Follow the existing code style
- Write clear, concise commit messages
- Add comments for complex logic
- Update documentation as needed

### 3. Write Tests

Add tests for new features or bug fixes:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_your_feature.py

# Run with coverage
pytest --cov=backend --cov=app
```

**Test requirements:**
- New features should include unit tests
- Bug fixes should include regression tests
- Aim for >80% code coverage

### 4. Code Quality Checks

Before committing, run:

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy backend/ app/

# Fix linting issues
ruff check . --fix
```

### 5. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: description of your feature"
```

**Commit message format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Example:**
```
feat(investigations): add pause/resume functionality

- Add pause_investigation method to InvestigationService
- Add API endpoints for pause/resume
- Add UI buttons in investigation workspace
- Add tests for pause/resume functionality
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Reference to related issues
- Screenshots (if UI changes)
- Test results

## Code Style Guidelines

### Python Code Style

- Follow **PEP 8** style guidelines
- Use **Black** for code formatting
- Use **Ruff** for linting
- Maximum line length: **100 characters**

### Code Organization

```
backend/
  agents/          # AI agents
  api/             # API routes
  database/        # Database models and migrations
  services/        # Business logic
  utils/           # Utility functions
  models/          # ML models
  middleware/      # Middleware components

app/
  components/      # Reusable UI components
  pages/           # Streamlit pages
  utils/           # Application utilities

tests/
  test_api.py      # API tests
  test_agents.py   # Agent tests
  test_models.py   # Model tests
  test_integration.py  # Integration tests
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of function.

    Longer description if needed, explaining what the function does,
    any important details, or usage examples.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is invalid
    """
    pass
```

### Type Hints

Always include type hints:

```python
from typing import List, Dict, Optional, Any
from uuid import UUID

def process_data(
    items: List[str],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    pass
```

## Testing Guidelines

### Test Structure

```python
def test_feature_name():
    """Test description of what is being tested."""
    # Arrange
    setup_data = create_test_data()
    
    # Act
    result = function_under_test(setup_data)
    
    # Assert
    assert result.expected_value == actual_value
```

### Test Coverage

- Unit tests for individual functions/classes
- Integration tests for API endpoints
- End-to-end tests for critical workflows
- Model tests for ML model functionality

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_api.py

# Specific test
pytest tests/test_api.py::test_create_investigation

# With coverage report
pytest --cov=backend --cov=app --cov-report=html
```

## Documentation Guidelines

### Code Documentation

- Add docstrings to all public functions/classes
- Include type hints for all parameters and return values
- Add inline comments for complex logic

### API Documentation

- API routes are automatically documented via FastAPI
- Ensure request/response models are well-documented
- Add example requests/responses in docstrings

### User Documentation

- Update `README.md` for user-facing changes
- Update `docs/` for architectural changes
- Add changelog entries for significant changes

## Database Changes

### Creating Migrations

When modifying database models:

1. **Update the model** in `backend/database/models.py`

2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "description of changes"
   ```

3. **Review the migration**:
   ```bash
   cat backend/database/migrations/versions/XXX_description.py
   ```

4. **Apply migration**:
   ```bash
   alembic upgrade head
   ```

5. **Test migration**:
   ```bash
   alembic downgrade -1
   alembic upgrade head
   ```

## Adding New Features

### Adding a New Agent

1. Create agent class in `backend/agents/`
2. Implement required methods
3. Add to orchestrator in `backend/agents/orchestrator.py`
4. Update agent prompts in `config/agent_prompts.yaml`
5. Add tests in `tests/test_agents.py`

### Adding a New API Endpoint

1. Create route function in appropriate router file
2. Add request/response models (Pydantic)
3. Add authentication if needed
4. Add tests in `tests/test_api.py`
5. Update API documentation

### Adding a New UI Page

1. Create page file in `app/pages/`
2. Add route in `app/app.py`
3. Create reusable components in `app/components/` if needed
4. Add navigation entry in `app/components/sidebar.py`
5. Test UI functionality

## Pull Request Process

1. **Ensure all tests pass**:
   ```bash
   pytest
   ```

2. **Ensure code quality checks pass**:
   ```bash
   black .
   ruff check .
   mypy backend/ app/
   ```

3. **Update documentation** as needed

4. **Create Pull Request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots for UI changes
   - Test coverage information

5. **Respond to review feedback** and make requested changes

6. **Maintainers will review** and merge when approved

## Issue Reporting

When reporting issues, include:

- **Description**: Clear description of the issue
- **Steps to Reproduce**: Detailed steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, dependencies versions
- **Screenshots/Logs**: If applicable

## Feature Requests

For feature requests:

- **Description**: Clear description of the feature
- **Use Case**: Why this feature is needed
- **Proposed Solution**: How you envision it working
- **Alternatives**: Other solutions you've considered

## Questions?

- Open an issue on GitHub
- Check existing documentation in `docs/`
- Review existing code for examples

## License

By contributing, you agree that your contributions will be licensed under the Apache License, Version 2.0.

Thank you for contributing! 🐅

