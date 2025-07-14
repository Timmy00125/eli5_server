# ELI5 Server Testing Guide

This document provides comprehensive information about testing the ELI5 Server application.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Test Coverage](#test-coverage)
- [Writing Tests](#writing-tests)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The ELI5 Server test suite provides comprehensive coverage of all application components including:

- **API Endpoints** - FastAPI route testing
- **Authentication** - JWT token and password security
- **Database Operations** - SQLAlchemy model and query testing
- **Service Layer** - Business logic validation
- **Data Validation** - Pydantic schema testing
- **Integration** - End-to-end workflow testing

### Test Framework

- **pytest** - Primary testing framework
- **httpx** - HTTP client for API testing
- **factory-boy** - Test data generation
- **pytest-cov** - Code coverage reporting
- **pytest-asyncio** - Async function testing

## 🏗️ Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py             # Shared fixtures and configuration
├── test_main.py            # API endpoint tests
├── test_auth.py            # Authentication system tests
├── test_database.py        # Database model and operation tests
├── test_services.py        # Service layer business logic tests
├── test_schemas.py         # Data validation and serialization tests
└── test_integration.py     # End-to-end integration tests
```

### Configuration Files

- `pytest.ini` - Pytest configuration and settings
- `conftest.py` - Shared test fixtures and utilities
- `run_tests.sh` - Test runner script with multiple options

## 🚀 Running Tests

### Quick Start

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
./run_tests.sh all

# Or using pytest directly
python -m pytest tests/ -v
```

### Test Runner Commands

The `run_tests.sh` script provides convenient commands:

```bash
# Run all tests with coverage
./run_tests.sh all

# Run specific test categories
./run_tests.sh unit          # Unit tests only
./run_tests.sh integration   # Integration tests only

# Run specific test files
./run_tests.sh test auth     # Authentication tests
./run_tests.sh test database # Database tests
./run_tests.sh test services # Service layer tests

# Generate comprehensive reports
./run_tests.sh report        # HTML and coverage reports
./run_tests.sh coverage      # Coverage report only

# Development utilities
./run_tests.sh watch         # Watch mode (re-run on changes)
./run_tests.sh lint          # Code quality checks
./run_tests.sh clean         # Clean test artifacts
```

### Direct Pytest Commands

```bash
# Basic test execution
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_auth.py -v

# Run specific test class
python -m pytest tests/test_auth.py::TestPasswordHashing -v

# Run specific test method
python -m pytest tests/test_auth.py::TestPasswordHashing::test_hash_password_creates_valid_hash -v

# Run tests matching pattern
python -m pytest tests/ -k "password" -v

# Stop on first failure
python -m pytest tests/ -x

# Show local variables on failure
python -m pytest tests/ -l

# Run in parallel (requires pytest-xdist)
python -m pytest tests/ -n auto
```

## 📊 Test Categories

### Unit Tests

**Location**: `test_auth.py`, `test_database.py`, `test_services.py`, `test_schemas.py`

Test individual components in isolation:

- Password hashing and verification
- JWT token creation and validation
- Database model relationships
- Service layer business logic
- Data validation schemas

**Run**: `./run_tests.sh unit`

### Integration Tests

**Location**: `test_main.py`, `test_integration.py`

Test component interactions and end-to-end workflows:

- API endpoint functionality
- External service integration (Gemini AI)
- Complete request/response cycles
- Error handling across layers

**Run**: `./run_tests.sh integration`

### Performance Tests

**Location**: `test_integration.py::TestPerformanceIntegration`

Test performance characteristics:

- Response time validation
- Memory usage stability
- Concurrent request handling
- Error recovery

**Run**: `./run_tests.sh performance`

## 📈 Test Coverage

### Coverage Goals

- **Minimum**: 80% overall coverage
- **Target**: 90%+ for critical components
- **Authentication**: 95%+ (security critical)
- **Database**: 90%+ (data integrity critical)

### Coverage Reports

```bash
# Generate HTML coverage report
./run_tests.sh coverage

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Configuration

Coverage settings in `pytest.ini`:

```ini
--cov=.                    # Cover all modules
--cov-report=term-missing  # Show missing lines
--cov-report=html          # Generate HTML report
--cov-fail-under=80        # Fail if below 80%
```

## ✍️ Writing Tests

### Test Structure

Follow the **Arrange-Act-Assert** pattern:

```python
def test_user_creation(self, test_session):
    """
    Test user creation functionality.

    Verifies:
    - User is created with correct data
    - Password is properly hashed
    - User is saved to database
    """
    # Arrange
    user_data = UserRegistration(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    # Act
    created_user = UserService.create_user(test_session, user_data)

    # Assert
    assert created_user is not None
    assert created_user.email == user_data.email
    assert verify_password(user_data.password, created_user.hashed_password)
```

### Test Documentation

Each test should include:

1. **Docstring** with description
2. **Verifies section** listing what is being tested
3. **Clear variable names**
4. **Meaningful assertions**

### Fixtures

Use fixtures for common test data:

```python
@pytest.fixture
def sample_user(test_session, sample_user_data):
    """Create a sample user in the test database."""
    from auth import hash_password

    user = User(
        email=sample_user_data["email"],
        username=sample_user_data["username"],
        hashed_password=hash_password(sample_user_data["password"])
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)

    return user
```

### Mocking External Services

Mock external dependencies:

```python
@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client for testing."""
    with patch('main.client') as mock_client:
        mock_response = Mock()
        mock_response.text = "Test explanation"
        mock_client.models.generate_content.return_value = mock_response
        yield mock_client
```

### Error Testing

Test both success and failure scenarios:

```python
def test_authenticate_user_wrong_password(self, test_session, sample_user):
    """Test authentication with wrong password."""
    user = authenticate_user(
        test_session,
        sample_user.email,
        "wrongpassword"
    )

    assert user is None
```

## 🔧 Test Configuration

### Environment Variables

Test environment uses specific configurations:

```python
os.environ["DATABASE_URL"] = "sqlite:///./test_eli5.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["GEMINI_API_KEY"] = "test-api-key"
```

### Test Database

- **SQLite** in-memory database for speed
- **Isolated transactions** for test independence
- **Automatic cleanup** after each test

### Pytest Markers

Use markers to categorize tests:

```python
@pytest.mark.slow
def test_large_dataset_processing():
    """Test that takes longer to run."""
    pass

@pytest.mark.integration
def test_full_api_workflow():
    """Integration test."""
    pass
```

Run specific markers:

```bash
# Skip slow tests
python -m pytest tests/ -m "not slow"

# Run only integration tests
python -m pytest tests/ -m "integration"
```

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          python -m pytest tests/ --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: tests
        entry: python -m pytest tests/ --tb=short
        language: system
        pass_filenames: false
        always_run: true
```

## 🐛 Troubleshooting

### Common Issues

#### Import Errors

```bash
# Error: ModuleNotFoundError
# Solution: Install dependencies
pip install -r requirements.txt

# Or add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Database Issues

```bash
# Error: Database connection failed
# Solution: Check DATABASE_URL in conftest.py

# Error: Table doesn't exist
# Solution: Ensure test database is created
python -c "from database import create_tables; create_tables()"
```

#### Fixture Issues

```bash
# Error: Fixture not found
# Solution: Check conftest.py imports and fixture definitions

# Error: Fixture scope issues
# Solution: Verify fixture scope (session, function, etc.)
```

### Debug Mode

Run tests with debugging:

```bash
# Show local variables on failure
python -m pytest tests/ -l

# Drop into debugger on failure
python -m pytest tests/ --pdb

# Verbose output
python -m pytest tests/ -vv

# Show print statements
python -m pytest tests/ -s
```

### Performance Issues

```bash
# Run tests in parallel
pip install pytest-xdist
python -m pytest tests/ -n auto

# Profile test execution
pip install pytest-profiling
python -m pytest tests/ --profile
```

## 📝 Best Practices

### Test Organization

1. **One test per function/method**
2. **Descriptive test names**
3. **Group related tests in classes**
4. **Use fixtures for common setup**

### Test Independence

1. **No test dependencies**
2. **Clean state between tests**
3. **Use transactions that rollback**
4. **Mock external services**

### Test Maintenance

1. **Update tests with code changes**
2. **Remove obsolete tests**
3. **Refactor test duplication**
4. **Keep test data minimal**

### Security Testing

1. **Test authentication edge cases**
2. **Validate input sanitization**
3. **Test permission boundaries**
4. **Verify error message safety**

## 🎯 Test Goals

- **Reliability**: Tests should pass consistently
- **Speed**: Test suite should run quickly
- **Maintainability**: Tests should be easy to update
- **Coverage**: Critical paths should be tested
- **Documentation**: Tests should serve as documentation

## 📞 Support

For testing issues:

1. Check this documentation
2. Review test output carefully
3. Use verbose mode for more details
4. Check similar tests for patterns
5. Refer to pytest documentation

Remember: Good tests are an investment in code quality and development speed!
