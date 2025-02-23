import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from main import app
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.databases import get_db

client = TestClient(app)

@pytest.mark.asyncio
async def test_database_connection():
    async for session in get_db():
        result = await session.execute(text("SELECT version()"))

        version = result.scalar()
        print(f"Database version: {version}")

def test_create_dream_entry():
    response = client.post(
        "/dreams/",
        json={
            "description": "I was flying over a misty forest at night",
            "emotions": ["excitement", "fear"]
        }
    )
    assert response.status_code == 201
    assert "id" in response.json()

def test_list_dreams():
    response = client.get("/dreams/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


