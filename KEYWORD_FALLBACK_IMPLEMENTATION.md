# Keyword Fallback Search Implementation Guide

## Overview
Implement a hybrid search system that uses semantic search first, then falls back to keyword-based database search when no results are found.

## Architecture

```
User Query: "Did I dream about flying?"
    ↓
┌─────────────────────────────────┐
│ 1. Semantic Search (threshold 0.5) │
└─────────────────────────────────┘
    ↓
   Found results? ──Yes──→ Return results
    ↓ No
┌─────────────────────────────────┐
│ 2. Keyword Database Search       │
│    (exact keyword matching)      │
└─────────────────────────────────┘
    ↓
   Return results (or empty)
```

## Implementation Steps

### Step 1: Database Migration - Add Keywords Column

**File:** `alembic/versions/xxx_add_keywords_column.py`

```python
"""add keywords column to dream_entries

Revision ID: xxx
Revises: yyy
Create Date: 2025-10-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'xxx'
down_revision = 'yyy'  # Replace with your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Add keywords column as array of strings
    op.add_column(
        'dream_entries',
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True)
    )

    # Create GIN index for fast array searching
    op.create_index(
        'ix_dream_entries_keywords',
        'dream_entries',
        ['keywords'],
        postgresql_using='gin'
    )


def downgrade():
    op.drop_index('ix_dream_entries_keywords', table_name='dream_entries')
    op.drop_column('dream_entries', 'keywords')
```

**Run migration:**
```bash
alembic upgrade head
```

---

### Step 2: Update DreamEntry Model

**File:** `src/backend/models/dreamentry.py`

```python
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from src.backend.databases import Base

class DreamEntry(Base):
    __tablename__ = 'dream_entries'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=False)
    interpretation = Column(Text)
    email = Column(String(100), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    emotion_tags = Column(String(100))
    keywords = Column(ARRAY(String), nullable=True)  # NEW FIELD
    image_url = Column(String(200))
    video_url = Column(String(200))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship with DreamVector
    vector = relationship("DreamVector", backref="dream_entry", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DreamEntry(id={self.id}, user_id={self.user_id}, timestamp={self.timestamp})>"
```

---

### Step 3: Update Dream Service to Store Keywords

**File:** `src/backend/services/dream_service.py`

**In `create_dream()` method:**

```python
async def create_dream(
    self,
    db: AsyncSession,
    user_id: int,
    description: str,
    title: Optional[str] = None,
    emotions: Optional[List[str]] = None,
    timestamp: Optional[datetime] = None
) -> DreamEntry:

    # Get AI interpretation
    interpretation, ai_title, ai_emotions, ai_keywords = self.ai_interpreter.interpret_dream(description, title)

    # Use provided values or AI-generated ones
    final_title = title or ai_title
    final_emotions = emotions if emotions else ai_emotions

    # Ensure title isn't too long
    if final_title:
        final_title = final_title[:35]

    # Create dream entry WITH KEYWORDS
    dream_entry = DreamEntry(
        user_id=user_id,
        title=final_title,
        description=description,
        interpretation=interpretation,
        emotion_tags=",".join(final_emotions) if final_emotions else None,
        keywords=ai_keywords,  # NEW: Store keywords in database
        timestamp=timestamp or datetime.utcnow()
    )

    try:
        db.add(dream_entry)
        await db.commit()
        await db.refresh(dream_entry)

        # Generate and store embedding
        try:
            embedding_service = get_embedding_service()
            await embedding_service.embed_dream_entry(db, dream_entry, keywords=ai_keywords)
            logger.info(f"Generated embedding for dream_id: {dream_entry.id}")
        except Exception as embed_error:
            logger.error(f"Failed to generate embedding for dream_id {dream_entry.id}: {str(embed_error)}")

    except Exception as e:
        print("debug: error adding dream to db: ", e)
        raise HTTPException(status_code=500, detail=str(e))

    return dream_entry
```

**In `update_dream()` method:**

```python
# If description changed, re-interpret the dream
new_keywords = []
if description is not None and description != dream.description:
    dream.description = description
    new_interpretation, new_title, new_emotions, new_keywords = self.ai_interpreter.interpret_dream(description, title)
    dream.interpretation = new_interpretation

    # Only update title if not explicitly provided
    if title is None:
        dream.title = new_title[:35] if new_title else dream.title

    # Only update emotions if not explicitly provided
    if emotions is None and new_emotions:
        dream.emotion_tags = ",".join(new_emotions)

    # Update keywords
    if new_keywords:
        dream.keywords = new_keywords  # NEW: Update keywords in database
```

---

### Step 4: Create Keyword Search Service

**File:** `src/backend/services/dream_retrieval_service.py`

Add this new method to `DreamRetrievalService` class:

```python
async def search_by_keywords(
    self,
    db: AsyncSession,
    user_id: int,
    query: str,
    top_k: Optional[int] = None
) -> List[Tuple[DreamEntry, float]]:
    """
    Search dreams by keyword matching in the keywords array.

    Args:
        db: Database session
        user_id: ID of the user whose dreams to search
        query: Query string (will search for words in this query)
        top_k: Number of results to return

    Returns:
        List of tuples (DreamEntry, match_score) ordered by relevance
    """
    try:
        from sqlalchemy import func, or_, and_

        # Extract keywords from query (split by spaces, remove common words)
        stop_words = {'i', 'did', 'have', 'dream', 'about', 'of', 'the', 'a', 'an'}
        query_keywords = [
            word.strip().lower()
            for word in query.split()
            if word.strip().lower() not in stop_words
        ]

        if not query_keywords:
            return []

        logger.info(f"Searching by keywords: {query_keywords}")

        # Build query to match any keyword in the array
        # Using PostgreSQL array overlap operator &&
        query_stmt = (
            select(DreamEntry)
            .where(
                and_(
                    DreamEntry.user_id == user_id,
                    DreamEntry.keywords.overlap(query_keywords)  # PostgreSQL array overlap
                )
            )
            .order_by(DreamEntry.timestamp.desc())
            .limit(top_k or self.default_top_k)
        )

        # Execute query
        result = await db.execute(query_stmt)
        dreams = result.scalars().all()

        # Calculate match score based on number of matching keywords
        results = []
        for dream in dreams:
            if dream.keywords:
                matches = len(set(dream.keywords) & set(query_keywords))
                total = len(query_keywords)
                score = matches / total if total > 0 else 0.0
                results.append((dream, score))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        logger.info(
            f"Found {len(results)} dreams by keyword matching for user {user_id}"
        )

        return results

    except Exception as e:
        logger.error(f"Error in keyword search: {str(e)}")
        raise
```

---

### Step 5: Update Dream Explorer Service with Fallback Logic

**File:** `src/backend/services/dream_explorer_service.py`

Modify the `ask_question()` method:

```python
async def ask_question(
    self,
    db: AsyncSession,
    user_id: int,
    question: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    top_k: Optional[int] = None
) -> Dict[str, Any]:
    """
    Answer a question about the user's dream history.
    Uses semantic search first, falls back to keyword search if no results.
    """
    # Validate question
    validate_query(question)

    logger.info(f"Processing question for user {user_id}: {question[:50]}...")

    try:
        # Check if this is a meta-question that needs all dreams
        meta_keywords = [
            'what emotions', 'which emotions', 'emotions appear', 'common emotions',
            'recurring', 'patterns', 'themes', 'most common', 'frequently',
            'usually', 'often', 'typically', 'what are my', 'tell me about my'
        ]

        is_meta_question = any(keyword in question.lower() for keyword in meta_keywords)

        if is_meta_question:
            # For meta-questions, retrieve ALL recent dreams
            logger.info(f"Detected meta-question, retrieving all recent dreams")
            with ErrorContext("retrieve all recent dreams"):
                from sqlalchemy import select
                result = await db.execute(
                    select(DreamEntry)
                    .where(DreamEntry.user_id == user_id)
                    .order_by(DreamEntry.timestamp.desc())
                    .limit(top_k or 20)
                )
                dreams = result.scalars().all()
                similar_dreams = [(dream, 1.0) for dream in dreams]
        else:
            # Try semantic search first
            with ErrorContext("retrieve relevant dreams"):
                similar_dreams = await self.retrieval_service.search_similar_dreams(
                    db=db,
                    user_id=user_id,
                    query=question,
                    top_k=top_k
                )

            # FALLBACK: If no results, try keyword search
            if len(similar_dreams) == 0:
                logger.info("Semantic search returned 0 results, trying keyword fallback")
                with ErrorContext("retrieve dreams by keyword"):
                    similar_dreams = await self.retrieval_service.search_by_keywords(
                        db=db,
                        user_id=user_id,
                        query=question,
                        top_k=top_k
                    )

                if len(similar_dreams) > 0:
                    logger.info(f"Keyword fallback found {len(similar_dreams)} dreams")

        # Format context
        context = self.format_dream_context(similar_dreams)

        # Format chat history
        chat_history = chat_history or []
        history_str = self.format_chat_history(chat_history)

        # Generate response using LangChain
        try:
            with ErrorContext("generate AI response", error_class=LLMGenerationError):
                response = await self.chain.arun(
                    context=context,
                    chat_history=history_str,
                    question=question
                )
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise LLMGenerationError(
                message="Failed to generate response. The AI service may be temporarily unavailable.",
                details={"error": str(e)}
            )

        # Update chat history
        updated_history = chat_history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": response}
        ]

        # Format dream summaries for response
        dream_summaries = [
            {
                "dream_id": dream.id,
                "title": dream.title or "Untitled",
                "date": dream.timestamp.isoformat() if dream.timestamp else None,
                "relevance_score": float(score)
            }
            for dream, score in similar_dreams
        ]

        logger.info(f"Successfully generated response for user {user_id}")

        return {
            "answer": response,
            "relevant_dreams": dream_summaries,
            "chat_history": updated_history
        }

    except (LLMGenerationError, DreamNotFoundError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ask_question: {str(e)}")
        raise LLMGenerationError(
            message="An unexpected error occurred while processing your question",
            details={"error": str(e)}
        )
```

---

### Step 6: Backfill Keywords for Existing Dreams

**File:** `backfill_keywords_for_existing_dreams.py`

```python
"""
Backfill keywords for existing dreams that don't have them
"""
import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from loguru import logger

from src.backend.models.dreamentry import DreamEntry
from src.backend.models.dream_vector import DreamVector
from src.backend.ai_interpreters.gemini_interpreter import GeminiDreamInterpreter
from src.backend.services.dream_embedding_service import get_embedding_service

load_dotenv()


async def backfill_keywords(user_id: int = None):
    """Extract and store keywords for existing dreams"""

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 60)
        print("BACKFILLING KEYWORDS FOR EXISTING DREAMS")
        print("=" * 60)

        # Build query for dreams without keywords
        query = select(DreamEntry).where(
            (DreamEntry.keywords == None) | (DreamEntry.keywords == [])
        )
        if user_id:
            query = query.where(DreamEntry.user_id == user_id)

        result = await db.execute(query)
        dreams = result.scalars().all()

        if not dreams:
            print("\n✓ All dreams already have keywords!")
            return

        print(f"\nFound {len(dreams)} dreams without keywords")

        # Initialize services
        interpreter = GeminiDreamInterpreter()
        embedding_service = get_embedding_service()

        success_count = 0
        error_count = 0

        for i, dream in enumerate(dreams, 1):
            try:
                print(f"\n[{i}/{len(dreams)}] Processing Dream {dream.id}: '{dream.title}'")
                print(f"  Description: {dream.description[:50]}...")

                # Use the interpreter to extract keywords
                _, _, _, keywords = interpreter.interpret_dream(
                    description=dream.description,
                    title=dream.title
                )

                if keywords:
                    # Update dream with keywords
                    dream.keywords = keywords
                    await db.commit()
                    await db.refresh(dream)

                    print(f"  ✓ Extracted keywords: {keywords}")

                    # Regenerate embedding with keywords
                    try:
                        await embedding_service.embed_dream_entry(db, dream, keywords=keywords)
                        print(f"  ✓ Updated embedding")
                    except Exception as embed_error:
                        logger.error(f"Failed to update embedding: {embed_error}")
                        print(f"  ⚠ Warning: Embedding update failed (dream saved with keywords)")

                    success_count += 1
                else:
                    print(f"  ⚠ No keywords extracted")
                    error_count += 1

            except Exception as e:
                print(f"  ✗ Error: {e}")
                logger.error(f"Error processing dream {dream.id}: {e}")
                error_count += 1

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✓ Successfully processed: {success_count}")
        print(f"✗ Errors/Skipped: {error_count}")
        print(f"Total: {len(dreams)}")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    user_id = None
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
        print(f"Backfilling keywords for user {user_id} only\n")
    else:
        print("Backfilling keywords for ALL users\n")

    asyncio.run(backfill_keywords(user_id))
```

---

## Testing Steps

### 1. Run Migration
```bash
alembic upgrade head
```

### 2. Restart Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Create New Dream
```bash
POST /dreams
{
  "description": "I was flying over mountains and felt amazing"
}
```

**Expected:** Keywords stored in database: `["flying", "mountains", "soaring", "freedom", "perspective"]`

### 4. Test Semantic Search
Query: "Did I dream about flying?"

**Expected Flow:**
1. Tries semantic search (threshold 0.5) → Returns 0 results
2. Falls back to keyword search → Finds dream (keyword: "flying")
3. Returns the flying dream ✓

### 5. Backfill Existing Dreams
```bash
python backfill_keywords_for_existing_dreams.py 1
```

---

## Performance Considerations

1. **GIN Index:** The `keywords` column uses GIN index for fast array searching
2. **Array Overlap:** PostgreSQL's `&&` operator is optimized for array comparisons
3. **Caching:** Consider caching frequently searched keywords

---

## Benefits

✅ **Guaranteed Matches:** If AI extracts keyword, it WILL be found
✅ **Fast:** Database index makes keyword search very fast
✅ **Smart Fallback:** Only uses keyword search when semantic search fails
✅ **Best of Both:** Semantic ranking + keyword precision

---

## Future Enhancements

- Add full-text search (PostgreSQL `tsvector`) for even better text matching
- Implement fuzzy keyword matching (Levenshtein distance)
- Add keyword analytics: most common keywords, trending keywords
- Support multi-language keywords
