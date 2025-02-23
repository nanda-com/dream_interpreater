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

# New tests for user registration and login
def test_register_user():
    response = client.post(
        "/users/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "securepassword"
        }
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}

def test_login_user_with_username():
    response = client.post(
        "/users/login",
        json={
            "username": "testuser",
            "password": "securepassword"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_user_with_email():
    response = client.post(
        "/users/login",
        json={
            "email": "testuser@example.com",
            "password": "securepassword"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
