"""
Manually run the keywords column migration
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv()


async def run_migration():
    """Add keywords column to dream_entries table"""

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        print("=" * 60)
        print("RUNNING KEYWORDS MIGRATION")
        print("=" * 60)

        try:
            # Check if column already exists
            result = await conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='dream_entries' AND column_name='keywords'
            """))

            if result.fetchone():
                print("\n✓ Column 'keywords' already exists!")
            else:
                print("\n1. Adding 'keywords' column...")
                await conn.execute(text("""
                    ALTER TABLE dream_entries
                    ADD COLUMN keywords TEXT[]
                """))
                print("   ✓ Column added successfully")

            # Check if index exists
            result = await conn.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename='dream_entries' AND indexname='ix_dream_entries_keywords'
            """))

            if result.fetchone():
                print("\n✓ Index 'ix_dream_entries_keywords' already exists!")
            else:
                print("\n2. Creating GIN index on 'keywords' column...")
                await conn.execute(text("""
                    CREATE INDEX ix_dream_entries_keywords
                    ON dream_entries
                    USING GIN (keywords)
                """))
                print("   ✓ Index created successfully")

            print("\n" + "=" * 60)
            print("MIGRATION COMPLETE!")
            print("=" * 60)

        except Exception as e:
            print(f"\n✗ Error during migration: {e}")
            raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())
