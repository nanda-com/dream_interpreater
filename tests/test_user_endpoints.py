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

def test_convert_guest_to_regular():
    # First create a guest user
    guest_response = client.post("/users/guest")
    assert guest_response.status_code == 200
    guest_data = guest_response.json()
    
    # Get the access token
    access_token = guest_data["access_token"]
    
    # Convert the guest user to a regular user
    convert_response = client.post(
        "/users/convert-guest",
        json={
            "name": "Converted User",
            "email": "converted@example.com",
            "password": "newpassword123"
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert convert_response.status_code == 200
    convert_data = convert_response.json()
    
    # Check that the user is no longer a guest
    assert convert_data["user"]["isGuest"] == False
    assert convert_data["user"]["name"] == "Converted User"
    assert convert_data["user"]["email"] == "converted@example.com"
    
    # Check that we can login with the new credentials
    login_response = client.post(
        "/users/login", 
        json={
            "email": "converted@example.com",
            "password": "newpassword123"
        }
    )
    assert login_response.status_code == 200
