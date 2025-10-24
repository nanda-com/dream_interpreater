# Keywords and Emotions Backfill Script

This script fills missing keywords and emotions for existing dreams and regenerates embeddings.

## Features

✅ Extracts keywords using AI (if missing)
✅ Extracts emotions using AI (if missing)
✅ Regenerates embeddings with new data
✅ Shows detailed progress for each dream
✅ Provides statistics about coverage
✅ Supports per-user processing
✅ Force mode to re-embed all dreams

---

## Usage

### 1. Show Statistics (Check Coverage)

See how many dreams need processing:

```bash
python backfill_keywords_and_emotions.py --stats
```

Output:
```
DATABASE STATISTICS
====================================================================
📊 Coverage Statistics:
  Total dreams: 5
  With keywords: 0 (0.0%)
  With emotions: 5 (100.0%)
  With both: 0 (0.0%)

⚠️  5 dreams need processing
```

### 2. Process All Dreams (All Users)

Fill missing keywords/emotions for all dreams:

```bash
python backfill_keywords_and_emotions.py
```

### 3. Process Specific User Only

Fill missing keywords/emotions for one user:

```bash
python backfill_keywords_and_emotions.py --user-id 53
```

### 4. Force Re-embed All Dreams

Re-extract keywords, emotions, and regenerate embeddings for ALL dreams (even if they already have data):

```bash
python backfill_keywords_and_emotions.py --force
```

⚠️ **Warning:** Force mode will process ALL dreams and make API calls to Gemini AI for each one.

### 5. Force Re-embed for Specific User

```bash
python backfill_keywords_and_emotions.py --user-id 53 --force
```

---

## What the Script Does

For each dream that's missing keywords or emotions:

1. **🤖 AI Extraction**
   - Calls Gemini AI to extract keywords (3-6 key content words)
   - Extracts emotions (2-4 primary emotions)

2. **💾 Database Update**
   - Saves keywords to `dream_entries.keywords` (ARRAY field)
   - Saves emotions to `dream_entries.emotion_tags` (TEXT field)

3. **🔄 Embedding Regeneration**
   - Creates new embedding with weighted components:
     - Keywords × 10 (individually repeated)
     - Description × 2
     - Emotions × 3
   - Updates `dream_vectors` table

---

## Example Output

```
======================================================================
[1/5] Processing Dream 123
======================================================================
  Title: Flying Dream
  Description: I was flying over mountains and felt amazing...

  Current state:
    Keywords: (missing)
    Emotions: joy, freedom

  🤖 Extracting metadata from AI...
  ✓ Extracted keywords: ['flying', 'mountains', 'soaring', 'sky']
  ⚠️  Emotions already present, keeping: joy, freedom

  💾 Saved updates: keywords

  🔄 Regenerating embedding...
  ✓ Embedding updated successfully

  ✅ Dream 123 processed successfully
```

---

## Final Summary

```
======================================================================
PROCESSING COMPLETE
======================================================================

📊 Summary:
  ✓ Successfully processed: 5
  ⚠️  Skipped (already complete): 0
  ✗ Errors: 0
  📈 Total dreams: 5

🎉 5 dreams now have enhanced search capabilities!
```

---

## Benefits

After running this script, your dreams will have:

✅ **Better Keyword Search** - AI-extracted keywords enable the 2nd level fallback
✅ **Better Text Search** - Enhanced embeddings improve semantic re-ranking
✅ **Better Emotion Queries** - "What emotions appear most?" will work properly
✅ **Better Pattern Detection** - More accurate pattern analysis in `/patterns`

---

## Troubleshooting

### No dreams found to process

If you see "All dreams already have keywords and emotions!", but search isn't working:

```bash
# Force re-embed to regenerate all embeddings
python backfill_keywords_and_emotions.py --force
```

### API Rate Limits

If you have many dreams, Gemini AI may rate limit. The script will continue after errors.

### Check specific user

```bash
# Show stats for user 53
python backfill_keywords_and_emotions.py --user-id 53 --stats
```

---

## Command Reference

| Command | Description |
|---------|-------------|
| `--stats` | Show statistics only, don't process |
| `--user-id 123` | Process only user 123's dreams |
| `--force` | Re-process ALL dreams (even complete ones) |
| `--help` | Show help message |

---

## Notes

- The script commits changes dream-by-dream (safe for interruption)
- Embedding updates happen after database save (data is preserved even if embedding fails)
- Progress is logged to console and loguru logs
- Safe to run multiple times (skips already-processed dreams)
