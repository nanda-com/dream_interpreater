import pytest
from httpx import AsyncClient
from sqlalchemy import text
from main import app
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.databases import get_db
import uuid


@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection."""
    async for session in get_db():
        result = await session.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"Database version: {version}")
        break  # Only need first session

@pytest.mark.asyncio
async def test_create_dream_entry(test_user_emails):
    """Test creating a dream entry with authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a test user
        unique_email = f"test_api_{uuid.uuid4().hex[:8]}@example.com"
        test_user_emails.append(unique_email)

        await client.post("/users/register", json={
            "name": "Test API User",
            "email": unique_email,
            "password": "testpassword123"
        })

        # Login to get token
        login_response = await client.post("/users/login", json={
            "email": unique_email,
            "password": "testpassword123"
        })
        auth_token = login_response.json()["access_token"]

        # Create dream entry
        response = await client.post(
            "/dreams/",
            json={
                "description": "I was flying over a misty forest at night",
                "emotions": ["excitement", "fear"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        assert "id" in response.json()

@pytest.mark.asyncio
async def test_list_dreams(test_user_emails):
    """Test listing dreams with authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a test user
        unique_email = f"test_api_{uuid.uuid4().hex[:8]}@example.com"
        test_user_emails.append(unique_email)

        await client.post("/users/register", json={
            "name": "Test API User",
            "email": unique_email,
            "password": "testpassword123"
        })

        # Login to get token
        login_response = await client.post("/users/login", json={
            "email": unique_email,
            "password": "testpassword123"
        })
        auth_token = login_response.json()["access_token"]

        # List dreams
        response = await client.get(
            "/dreams/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


