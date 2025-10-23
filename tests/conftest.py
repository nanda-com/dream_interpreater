"""
Pytest configuration and fixtures for all tests.
"""
import pytest
import os
from unittest.mock import Mock, patch

# Set test environment variables before importing app
os.environ["TESTING"] = "1"
# Don't override GOOGLE_API_KEY or JWT_SECRET or PostgreSQL_URL - use the ones from .env
# Only set them if they're not already set
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "test-api-key"
if "JWT_SECRET" not in os.environ:
    os.environ["JWT_SECRET"] = "test-secret-key"
# Let PostgreSQL_URL come from .env file


@pytest.fixture(scope="session", autouse=True)
def disable_rate_limiting():
    """Disable rate limiting for all tests."""
    # Mock the limiter to bypass rate limiting during tests
    with patch("src.backend.utils.rate_limiter.limiter.limit") as mock_limit:
        # Make the decorator a no-op
        mock_limit.side_effect = lambda func_or_str: (
            lambda f: f if callable(func_or_str) else lambda f: f
        )
        yield mock_limit


@pytest.fixture(autouse=True)
def mock_limiter_decorator():
    """Mock rate limiter decorator for each test."""
    def noop_decorator(*args, **kwargs):
        def decorator(f):
            return f
        return decorator if not callable(args[0]) else args[0]

    with patch("src.backend.api.endpoints.dream_explorer.limiter.limit", side_effect=noop_decorator):
        yield
