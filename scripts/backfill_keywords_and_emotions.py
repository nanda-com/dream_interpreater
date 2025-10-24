"""
Backfill keywords and emotions for existing dreams that don't have them,
and regenerate embeddings with the new data.
"""
import asyncio
import os
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from loguru import logger

from src.backend.models.dreamentry import DreamEntry
from src.backend.models.dream_vector import DreamVector
from src.backend.ai_interpreters.gemini_interpreter import GeminiDreamInterpreter
from src.backend.services.dream_embedding_service import get_embedding_service

load_dotenv()


async def backfill_keywords_and_emotions(user_id: int = None, force_reembed: bool = False):
    """
    Extract and store keywords and emotions for existing dreams,
    then regenerate embeddings.

    Args:
        user_id: If provided, only process dreams for this user
        force_reembed: If True, re-embed all dreams even if they have keywords/emotions
    """

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 70)
        print("BACKFILLING KEYWORDS AND EMOTIONS FOR EXISTING DREAMS")
        print("=" * 70)

        # Build query for dreams without keywords or emotions
        if force_reembed:
            print("\n⚠️  Force re-embed mode: Processing ALL dreams")
            query = select(DreamEntry)
        else:
            query = select(DreamEntry).where(
                or_(
                    DreamEntry.keywords == None,
                    DreamEntry.keywords == [],
                    DreamEntry.emotion_tags == None,
                    DreamEntry.emotion_tags == ""
                )
            )

        if user_id:
            query = query.where(DreamEntry.user_id == user_id)

        result = await db.execute(query)
        dreams = result.scalars().all()

        if not dreams:
            print("\n✓ All dreams already have keywords and emotions!")
            return

        print(f"\nFound {len(dreams)} dreams to process")

        # Initialize services
        interpreter = GeminiDreamInterpreter()
        embedding_service = get_embedding_service()

        success_count = 0
        error_count = 0
        skipped_count = 0

        for i, dream in enumerate(dreams, 1):
            try:
                print(f"\n{'=' * 70}")
                print(f"[{i}/{len(dreams)}] Processing Dream {dream.id}")
                print(f"{'=' * 70}")
                print(f"  Title: {dream.title or 'Untitled'}")
                print(f"  Description: {dream.description[:80]}...")

                # Check what's missing
                needs_keywords = not dream.keywords or len(dream.keywords) == 0
                needs_emotions = not dream.emotion_tags or dream.emotion_tags.strip() == ""

                if not force_reembed and not needs_keywords and not needs_emotions:
                    print(f"  ⚠️  Already has keywords and emotions, skipping")
                    skipped_count += 1
                    continue

                print(f"\n  Current state:")
                print(f"    Keywords: {dream.keywords or '(missing)'}")
                print(f"    Emotions: {dream.emotion_tags or '(missing)'}")

                # Use the interpreter to extract keywords and emotions
                print(f"\n  🤖 Extracting metadata from AI...")
                interpretation, ai_title, ai_emotions, ai_keywords = interpreter.interpret_dream(
                    description=dream.description,
                    title=dream.title
                )

                # Track what was updated
                updated_fields = []

                # Update keywords if missing or force mode
                if needs_keywords or force_reembed:
                    if ai_keywords:
                        dream.keywords = ai_keywords
                        updated_fields.append("keywords")
                        print(f"  ✓ Extracted keywords: {ai_keywords}")
                    else:
                        print(f"  ⚠️  No keywords extracted")

                # Update emotions if missing or force mode
                if needs_emotions or force_reembed:
                    if ai_emotions:
                        dream.emotion_tags = ",".join(ai_emotions)
                        updated_fields.append("emotions")
                        print(f"  ✓ Extracted emotions: {ai_emotions}")
                    else:
                        print(f"  ⚠️  No emotions extracted")

                # Save changes to database
                if updated_fields:
                    await db.commit()
                    await db.refresh(dream)
                    print(f"\n  💾 Saved updates: {', '.join(updated_fields)}")

                # Regenerate embedding with new keywords and emotions
                print(f"\n  🔄 Regenerating embedding...")
                try:
                    await embedding_service.embed_dream_entry(
                        db,
                        dream,
                        keywords=dream.keywords
                    )
                    print(f"  ✓ Embedding updated successfully")
                except Exception as embed_error:
                    logger.error(f"Failed to update embedding: {embed_error}")
                    print(f"  ⚠️  Warning: Embedding update failed (dream saved with new data)")

                success_count += 1
                print(f"\n  ✅ Dream {dream.id} processed successfully")

            except Exception as e:
                print(f"\n  ✗ Error processing dream {dream.id}: {e}")
                logger.error(f"Error processing dream {dream.id}: {e}", exc_info=True)
                error_count += 1
                continue

        # Final summary
        print("\n" + "=" * 70)
        print("PROCESSING COMPLETE")
        print("=" * 70)
        print(f"\n📊 Summary:")
        print(f"  ✓ Successfully processed: {success_count}")
        print(f"  ⚠️  Skipped (already complete): {skipped_count}")
        print(f"  ✗ Errors: {error_count}")
        print(f"  📈 Total dreams: {len(dreams)}")

        if success_count > 0:
            print(f"\n🎉 {success_count} dreams now have enhanced search capabilities!")

    await engine.dispose()


async def show_statistics(user_id: int = None):
    """Show statistics about keywords and emotions coverage"""

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("\n" + "=" * 70)
        print("DATABASE STATISTICS")
        print("=" * 70)

        # Total dreams
        query = select(DreamEntry)
        if user_id:
            query = query.where(DreamEntry.user_id == user_id)

        result = await db.execute(query)
        total_dreams = len(result.scalars().all())

        # Dreams with keywords
        query = select(DreamEntry).where(
            DreamEntry.keywords.isnot(None),
            DreamEntry.keywords != []
        )
        if user_id:
            query = query.where(DreamEntry.user_id == user_id)

        result = await db.execute(query)
        dreams_with_keywords = len(result.scalars().all())

        # Dreams with emotions
        query = select(DreamEntry).where(
            DreamEntry.emotion_tags.isnot(None),
            DreamEntry.emotion_tags != ""
        )
        if user_id:
            query = query.where(DreamEntry.user_id == user_id)

        result = await db.execute(query)
        dreams_with_emotions = len(result.scalars().all())

        # Dreams with both
        query = select(DreamEntry).where(
            DreamEntry.keywords.isnot(None),
            DreamEntry.keywords != [],
            DreamEntry.emotion_tags.isnot(None),
            DreamEntry.emotion_tags != ""
        )
        if user_id:
            query = query.where(DreamEntry.user_id == user_id)

        result = await db.execute(query)
        dreams_with_both = len(result.scalars().all())

        print(f"\n📊 Coverage Statistics:")
        print(f"  Total dreams: {total_dreams}")
        print(f"  With keywords: {dreams_with_keywords} ({dreams_with_keywords/total_dreams*100:.1f}%)" if total_dreams > 0 else "  With keywords: 0 (0%)")
        print(f"  With emotions: {dreams_with_emotions} ({dreams_with_emotions/total_dreams*100:.1f}%)" if total_dreams > 0 else "  With emotions: 0 (0%)")
        print(f"  With both: {dreams_with_both} ({dreams_with_both/total_dreams*100:.1f}%)" if total_dreams > 0 else "  With both: 0 (0%)")

        missing = total_dreams - dreams_with_both
        if missing > 0:
            print(f"\n⚠️  {missing} dreams need processing")

    await engine.dispose()


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description='Backfill keywords and emotions for dreams'
    )
    parser.add_argument(
        '--user-id',
        type=int,
        help='Process only dreams for this user ID'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-embed all dreams even if they have keywords/emotions'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics only, do not process'
    )

    args = parser.parse_args()

    if args.stats:
        # Show statistics only
        asyncio.run(show_statistics(args.user_id))
    else:
        # Run backfill
        if args.user_id:
            print(f"Processing dreams for user {args.user_id}")
        else:
            print("Processing dreams for ALL users")

        if args.force:
            print("⚠️  FORCE MODE: Will re-embed ALL dreams\n")

        asyncio.run(backfill_keywords_and_emotions(args.user_id, args.force))
