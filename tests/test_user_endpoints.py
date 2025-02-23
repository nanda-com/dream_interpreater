import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/users/register", json={
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}

def test_login_user():
    response = client.post("/users/login", json={
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_user():
    response = client.post("/users/login", json={
        "email": "invaliduser@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid username or password"}
