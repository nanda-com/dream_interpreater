# Testing Guide

## Overview

This document provides instructions for running the test suite for the Dream Journal AI application. The test suite includes 60 automated tests covering all features including Dream Explorer, user authentication, and API endpoints.

## Prerequisites

1. **Python 3.9+** installed
2. **PostgreSQL database** running and accessible
3. **Environment variables** configured in `.env` file
4. **Virtual environment** set up

## Required Environment Variables

Ensure your `.env` file contains:

```bash
# Database
PostgreSQL_URL=postgresql+asyncpg://user:password@host:port/database

# AI Service
GOOGLE_API_KEY=your_gemini_api_key
LLM_MODEL_NAME=gemini-2.5-flash-lite

# Authentication
JWT_SECRET=your_jwt_secret
GOOGLE_CLIENT_ID=your_google_client_id

# Testing (automatically set by test suite)
TESTING=1
```

## Setup Instructions

### 1. Activate Virtual Environment

```bash
# Navigate to project directory
cd /path/to/ai-dream-journal

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows
```

### 2. Install Dependencies (if not already installed)

```bash
pip install -r requirements.txt
```

### 3. Verify Database Connection

```bash
# Test database connection
pytest tests/test_api.py::test_database_connection -v
```

## Running Tests

### Run All Tests

```bash
# Run all 60 tests with verbose output
pytest tests/ -v

# Run all tests with detailed output
pytest tests/ -v -s

# Run all tests and save results to file
pytest tests/ -v 2>&1 | tee test_results.log
```

**Expected Result:**
```
======================= 60 passed, 3 warnings in ~60s ========================
```

### Run Specific Test Categories

#### 1. Dream Explorer Tests (46 tests)

```bash
# Run all Dream Explorer feature tests
pytest tests/test_dream_embedding_service.py \
       tests/test_dream_retrieval_service.py \
       tests/test_dream_explorer_service.py \
       tests/test_dream_explorer_endpoints.py -v
```

**Components tested:**
- Embedding Service (13 tests)
- Retrieval Service (12 tests)
- Explorer Service (13 tests)
- API Endpoints (14 tests)

#### 2. User Authentication Tests (4 tests)

```bash
# Run user authentication and registration tests
pytest tests/test_user_endpoints.py -v
```

**Tests:**
- User registration
- User login
- Invalid credentials handling
- Guest user conversion

#### 3. Dream API Tests (3 tests)

```bash
# Run dream creation and listing tests
pytest tests/test_api.py -v
```

**Tests:**
- Database connection
- Dream entry creation
- Dream listing with authentication

### Run Individual Test Files

```bash
# Embedding service tests (13 tests)
pytest tests/test_dream_embedding_service.py -v

# Retrieval service tests (12 tests)
pytest tests/test_dream_retrieval_service.py -v

# Explorer service tests (13 tests)
pytest tests/test_dream_explorer_service.py -v

# API endpoint tests (14 tests)
pytest tests/test_dream_explorer_endpoints.py -v

# User endpoint tests (4 tests)
pytest tests/test_user_endpoints.py -v

# Dream API tests (3 tests)
pytest tests/test_api.py -v
```

### Run Specific Test Functions

```bash
# Run a single test by name
pytest tests/test_user_endpoints.py::test_register_user -v

# Run multiple specific tests
pytest tests/test_api.py::test_database_connection \
       tests/test_user_endpoints.py::test_login_user -v
```

## Test Output Options

### Verbose Output with Line Numbers

```bash
# Show detailed test output with line numbers on failures
pytest tests/ -v --tb=line
```

### Show Print Statements

```bash
# Display print statements and logs during test execution
pytest tests/ -v -s
```

### Stop on First Failure

```bash
# Stop immediately when a test fails
pytest tests/ -v -x
```

### Run Only Failed Tests

```bash
# Re-run only tests that failed in the last run
pytest tests/ -v --lf
```

### Show Test Duration

```bash
# Show slowest 10 tests
pytest tests/ -v --durations=10
```

## Test Coverage

### Generate Coverage Report

```bash
# Install coverage tool
pip install pytest-cov

# Run tests with coverage
pytest tests/ --cov=src/backend --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
# OR
xdg-open htmlcov/index.html  # Linux
```

## Understanding Test Results

### Successful Test Run

```
tests/test_dream_embedding_service.py::TestDreamEmbeddingService::test_service_initialization PASSED
tests/test_dream_embedding_service.py::TestDreamEmbeddingService::test_generate_embedding PASSED
...
======================= 60 passed, 3 warnings in 58.61s ========================
```

- **PASSED**: Test executed successfully
- **Warnings**: Non-critical deprecation warnings (expected)

### Common Warnings (Expected)

1. **PendingDeprecationWarning: multipart** - Starlette library warning, safe to ignore
2. **DeprecationWarning: on_event** - FastAPI suggests using lifespan handlers, non-critical

### Test Failure Example

```
FAILED tests/test_user_endpoints.py::test_register_user - assert 400 == 200
```

If tests fail:
1. Check database connection
2. Verify environment variables are set
3. Ensure virtual environment is activated
4. Check if database has required tables

## Test Data Cleanup

Tests automatically clean up after themselves:
- All test users are deleted after each test
- Database connections are properly disposed
- No manual cleanup required

Test users use unique UUID-based emails like:
- `testuser_abc12345@example.com`
- `test_api_def67890@example.com`
- `converted_ghi13579@example.com`

## Troubleshooting

### Issue: Database Connection Errors

**Error:** `OSError: Connect call failed`

**Solution:**
```bash
# Check PostgreSQL is running
psql -U your_username -d your_database -c "SELECT version();"

# Verify PostgreSQL_URL in .env
echo $PostgreSQL_URL
```

### Issue: Rate Limiting Errors

**Error:** `assert 500 == 200` (Rate limit issues)

**Solution:**
- Tests automatically disable rate limiting via `TESTING=1`
- If issues persist, check `conftest.py` is properly configured

### Issue: Event Loop Errors

**Error:** `RuntimeError: Task attached to a different loop`

**Solution:**
- This should be automatically handled by the test fixtures
- If it occurs, ensure you're using `AsyncClient` in async tests

### Issue: Import Errors

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Ensure pytest.ini is present in project root
cat pytest.ini

# Should contain:
# [pytest]
# pythonpath = .
```

### Issue: Google API Key Errors

**Error:** `ValueError: GOOGLE_API_KEY environment variable is required`

**Solution:**
```bash
# Set Google API key in .env
echo "GOOGLE_API_KEY=your_actual_api_key" >> .env

# Or export temporarily
export GOOGLE_API_KEY=your_actual_api_key
```

## Continuous Integration

### Running Tests in CI/CD

Example GitHub Actions workflow:

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt

      - name: Run tests
        env:
          PostgreSQL_URL: postgresql+asyncpg://postgres:postgres@localhost/test_db
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
          JWT_SECRET: test-secret
        run: |
          source venv/bin/activate
          pytest tests/ -v
```

## Performance Benchmarks

Typical test execution times:
- **All tests (60)**: ~60 seconds
- **Dream Explorer tests (46)**: ~45 seconds
- **User endpoint tests (4)**: ~8 seconds
- **Dream API tests (3)**: ~5 seconds

## Test Architecture

### Test Files Structure

```
tests/
├── conftest.py                          # Shared fixtures and configuration
├── pytest.ini                           # Pytest configuration
├── test_api.py                          # Dream API tests (3 tests)
├── test_user_endpoints.py               # User authentication tests (4 tests)
├── test_dream_embedding_service.py      # Embedding service tests (13 tests)
├── test_dream_retrieval_service.py      # Retrieval service tests (12 tests)
├── test_dream_explorer_service.py       # Explorer service tests (13 tests)
└── test_dream_explorer_endpoints.py     # API endpoint tests (14 tests)
```

### Key Testing Concepts

1. **Async Tests**: All tests use `@pytest.mark.asyncio` for async operations
2. **Mocking**: LangChain and external APIs are mocked for unit tests
3. **Fixtures**: Shared test data and setup via pytest fixtures
4. **Isolation**: Each test gets fresh database connections
5. **Cleanup**: Automatic cleanup of test data after each test

## Quick Reference Commands

```bash
# Activate environment and run all tests
source venv/bin/activate && pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src/backend -v

# Run specific test category
pytest tests/test_dream_explorer_*.py -v

# Debug a failing test
pytest tests/test_user_endpoints.py::test_register_user -v -s --tb=long

# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -v -n auto
```

## Support

If you encounter issues not covered in this guide:
1. Check the test output carefully for error messages
2. Review `full_test_results.log` if tests were run with output redirection
3. Ensure all environment variables are properly set
4. Verify database connectivity and permissions
5. Check that virtual environment has all required packages

## Summary

- **Total Tests**: 60
- **Test Files**: 6
- **Expected Pass Rate**: 100%
- **Average Run Time**: ~60 seconds
- **Automatic Cleanup**: Yes
- **CI/CD Ready**: Yes
