"""
Manual cleanup script for test data in the database.
Run this to remove any leftover test users and their dreams.
"""
import asyncio
from sqlalchemy import text
from src.backend.databases import AsyncSessionLocal


async def cleanup_test_data():
    """Remove all test users and their associated data from the database."""
    print("🧹 Starting test data cleanup...")

    async with AsyncSessionLocal() as session:
        # Find all test users (various test email patterns)
        test_patterns = [
            "testuser_%@example.com",
            "test_api_%@example.com",
            "converted_%@example.com",
            "Test API User"  # Also search by name
        ]

        total_deleted = 0

        for pattern in test_patterns:
            # Find users by email pattern or name
            if "@" in pattern:
                result = await session.execute(
                    text("SELECT id, email, name FROM users WHERE email LIKE :pattern"),
                    {"pattern": pattern}
                )
            else:
                result = await session.execute(
                    text("SELECT id, email, name FROM users WHERE name = :pattern"),
                    {"pattern": pattern}
                )

            users = result.fetchall()

            for user in users:
                user_id, email, name = user
                print(f"  Deleting user: {name} ({email})")

                # Count dreams
                dream_count = await session.execute(
                    text("SELECT COUNT(*) FROM dream_entries WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                num_dreams = dream_count.scalar()

                if num_dreams > 0:
                    print(f"    - Found {num_dreams} dream(s)")

                # Delete dream vectors
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

                total_deleted += 1

        await session.commit()
        print(f"✅ Cleanup complete! Deleted {total_deleted} test user(s) and their data.")


if __name__ == "__main__":
    asyncio.run(cleanup_test_data())
