import pytest
from httpx import AsyncClient
from main import app
import uuid

@pytest.mark.asyncio
async def test_register_user(test_user_emails):
    """Test user registration."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Use unique email to avoid conflicts
        unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        test_user_emails.append(unique_email)  # Register for cleanup

        response = await client.post("/users/register", json={
            "name": "Test User",
            "email": unique_email,
            "password": "testpassword"
        })
        assert response.status_code == 200
        assert response.json() == {"message": "User registered successfully"}

@pytest.mark.asyncio
async def test_login_user(test_user_emails):
    """Test user login after registration."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register first
        unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        test_user_emails.append(unique_email)  # Register for cleanup

        await client.post("/users/register", json={
            "name": "Test User",
            "email": unique_email,
            "password": "testpassword"
        })

        # Then login
        response = await client.post("/users/login", json={
            "email": unique_email,
            "password": "testpassword"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_invalid_user(test_user_emails):
    """Test login with invalid credentials."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/users/login", json={
            "email": "invaliduser@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 400
        assert response.json() == {"detail": "Invalid username or password"}

@pytest.mark.asyncio
async def test_convert_guest_to_regular(test_user_emails):
    """Test converting guest user to regular user."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First create a guest user
        guest_response = await client.post("/users/guest")
        assert guest_response.status_code == 200
        guest_data = guest_response.json()

        # Get the access token
        access_token = guest_data["access_token"]

        # Use unique email
        unique_email = f"converted_{uuid.uuid4().hex[:8]}@example.com"
        test_user_emails.append(unique_email)  # Register for cleanup

        # Convert the guest user to a regular user
        convert_response = await client.post(
            "/users/convert-guest",
            json={
                "name": "Converted User",
                "email": unique_email,
                "password": "newpassword123"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert convert_response.status_code == 200
        convert_data = convert_response.json()

        # Check that the user is no longer a guest
        assert convert_data["user"]["isGuest"] == False
        assert convert_data["user"]["name"] == "Converted User"
        assert convert_data["user"]["email"] == unique_email

        # Check that we can login with the new credentials
        login_response = await client.post(
            "/users/login",
            json={
                "email": unique_email,
                "password": "newpassword123"
            }
        )
        assert login_response.status_code == 200
