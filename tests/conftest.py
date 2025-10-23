"""
Pytest configuration and fixtures for all tests.
"""
import pytest
import os
from dotenv import load_dotenv
from unittest.mock import Mock, patch
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file first
load_dotenv()

# Set test environment variables before importing app
os.environ["TESTING"] = "1"
# Don't override GOOGLE_API_KEY or JWT_SECRET or PostgreSQL_URL - use the ones from .env
# Only set them if they're not already set
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "test-api-key"
if "JWT_SECRET" not in os.environ:
    os.environ["JWT_SECRET"] = "test-secret-key"
# Let PostgreSQL_URL come from .env file


@pytest.fixture(scope="function")
def test_user_emails():
    """
    Track test user emails for cleanup.
    Tests can register emails here for automatic cleanup.
    """
    emails = []
    yield emails


@pytest.fixture(scope="function", autouse=True)
async def cleanup_test_data(test_user_emails):
    """
    Track test data and clean up after each test.
    - Deletes test users from database
    - Cleans up database connections to prevent event loop conflicts
    """
    yield

    # Cleanup test data (delete test users and their dreams)
    if test_user_emails:
        try:
            from src.backend.databases import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                from sqlalchemy import text
                for email in test_user_emails:
                    # First get the user_id
                    result = await session.execute(
                        text("SELECT id FROM users WHERE email = :email"),
                        {"email": email}
                    )
                    user = result.fetchone()

                    if user:
                        user_id = user[0]

                        # Delete dream vectors first (they have CASCADE but being explicit)
                        await session.execute(
                            text("DELETE FROM dream_vectors WHERE user_id = :user_id"),
                            {"user_id": user_id}
                        )

                        # Delete dreams
                        await session.execute(
                            text("DELETE FROM dream_entries WHERE user_id = :user_id"),
                            {"user_id": user_id}
                        )

                        # Delete user
                        await session.execute(
                            text("DELETE FROM users WHERE id = :user_id"),
                            {"user_id": user_id}
                        )

                await session.commit()
        except Exception as e:
            print(f"Warning: Failed to cleanup test users: {e}")

    # Force cleanup of database connections after each test
    # This prevents "attached to a different loop" errors
    try:
        from src.backend.databases import engine
        if engine:
            # Dispose all connections in the pool to prevent event loop conflicts
            await engine.dispose()
            # Recreate the pool for the next test
            from sqlalchemy.ext.asyncio import create_async_engine
            from src.backend import databases
            import os
            databases.engine = create_async_engine(
                os.getenv("PostgreSQL_URL"),
                pool_size=20,
                max_overflow=10,
                pool_timeout=30,
                pool_pre_ping=True
            )
            # Update the session factory
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy.ext.asyncio import AsyncSession
            databases.AsyncSessionLocal = sessionmaker(
                bind=databases.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
    except Exception as e:
        print(f"Warning: Failed to cleanup connections: {e}")


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


@pytest.fixture(scope="session", autouse=True)
def dispose_db_engine():
    """Dispose database engine after all tests to prevent event loop issues."""
    yield
    # Import engine here to ensure it's initialized
    try:
        from src.backend.databases import engine
        if engine:
            # Use asyncio.run to properly dispose the engine
            asyncio.run(engine.dispose())
    except Exception:
        pass  # Ignore disposal errors at cleanup
