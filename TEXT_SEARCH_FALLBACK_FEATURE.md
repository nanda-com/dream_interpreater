# Text Search Fallback Feature (Option #6)

## Overview
Implement a third-level fallback using PostgreSQL full-text search to find dreams when both semantic search and keyword matching fail. This guarantees finding dreams if the exact word appears anywhere in the description.

---

## How It Works

**Search Flow:**
```
User Query: "Did I dream about flying?"
    ↓
1. Semantic Search (threshold 0.5) → No results
    ↓
2. Keyword Array Search (database keywords field) → No results
    ↓
3. Text Pattern Search (ILIKE in description) → Finds "flying" in description!
    ↓
Return results
```

**Key Difference from #5:**
- **Option #5:** Searches AI-extracted keywords (depends on AI accuracy)
- **Option #6:** Searches actual description text (100% reliable if word exists)

---

## Benefits

✅ **Guaranteed Match:** If word appears in description, it WILL be found
✅ **No AI Dependency:** Searches raw text, not AI-extracted data
✅ **Handles Edge Cases:** Finds dreams even when AI missed the keyword
✅ **Case-Insensitive:** Works regardless of capitalization

---

## Implementation Steps

### Step 1: Add Text Search Method
Create a new method in `DreamRetrievalService` class:
- Extract search terms from query (remove stop words, strip punctuation)
- Build PostgreSQL ILIKE query for each term
- Filter dreams where description contains any search term
- Return results ordered by timestamp (most recent first)

### Step 2: Update Fallback Logic
Modify `DreamExplorerService.ask_question()` method:
- If semantic search returns 0 results → try keyword search
- If keyword search returns 0 results → try text search
- Log which method found the results

### Step 3: Add Optional Semantic Ranking
After finding dreams via text search:
- Calculate semantic similarity for each dream
- Re-rank results by similarity score
- This provides better ordering than just timestamp

---

## Performance Considerations

**Speed:** Text search (ILIKE) is slower than indexed searches, which is why it's used as the last fallback.

**Optimization:** Consider adding a PostgreSQL GIN index on description field using `to_tsvector` for faster full-text search (optional enhancement).

---

## Example Flow

**Query:** "Did I dream about water?"

**Fallback Chain:**
1. Semantic search → 0 results (similarity < 0.5)
2. Keyword search → 0 results (AI extracted keywords: "ocean", "swimming" - missed "water")
3. Text search → **Finds dream!** (description: "I was in water feeling calm")

**Result:** User gets their dream even though AI didn't extract "water" as a keyword.

---

## When to Use This Feature

**Best for:**
- Dreams where AI missed important keywords
- Specific word searches that didn't make it into keyword extraction
- Edge cases where semantic similarity is very low
- Typos or unusual words that embeddings don't handle well

**Not needed if:**
- Semantic + keyword search already work well (current 2-level fallback is sufficient)
- Performance is more important than 100% recall

---

## Implementation Checklist

- [ ] Add `search_by_text()` method to `DreamRetrievalService`
- [ ] Extract search terms (remove stop words, punctuation)
- [ ] Build ILIKE query for description field
- [ ] Add third fallback to `DreamExplorerService`
- [ ] (Optional) Add semantic re-ranking of text search results
- [ ] (Optional) Add GIN index for faster text search
- [ ] Test with queries that fail first two fallbacks

---

## Estimated Implementation Time

**Basic implementation:** 15-20 minutes
**With semantic re-ranking:** 30 minutes
**With GIN indexing:** 45 minutes

---

## Trade-offs

**Pros:**
- Maximum recall (finds everything)
- No dependency on AI accuracy
- Simple to understand and maintain

**Cons:**
- Slower than indexed searches
- May return false positives (e.g., "flying" in "terrifying")
- No semantic understanding (exact word match only)

---

## Recommended Approach

Start with the **2-level fallback** (semantic + keyword) currently implemented. Add text search (3rd fallback) only if you notice cases where both methods fail but the word exists in the description.

**Monitor logs** to see how often keyword fallback is triggered. If it's rare, text search may not be needed.
