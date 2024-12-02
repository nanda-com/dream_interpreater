import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

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