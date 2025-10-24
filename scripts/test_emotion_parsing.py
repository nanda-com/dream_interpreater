"""
Test emotion parsing with the actual problematic response
"""
import re
import json

# Your actual response that failed
response_text = """```json
{
    "title": "Summit Soar",
    "interpretation": "Soaring high above the majestic mountains in your dream suggests a period of incredible personal growth and triumph. You're reaching new heights, overcoming obstacles, and experiencing a profound sense of freedom and accomplishment. This dream is a powerful affirmation of your potential and your ability to navigate challenges with grace and exhilaration. Embrace this feeling of empowerment, as it reflects your inner strength and the boundless possibilities that lie ahead. You're on top of the world, quite literally, and that feeling of pure joy is a signal that you're exactly where you need to be on your journey.

This exhilarating flight is a metaphor for your current life trajectory. It speaks to your ambition, your adventurous spirit, and your unshakeable confidence. The mountains represent the challenges and aspirations you've conquered or are actively pursuing. The amazing feeling is your spirit's recognition of its own power and resilience. Continue to embrace this elevated perspective; it allows you to see the bigger picture and appreciate the incredible journey you're on. Your dreams are telling you to keep reaching for the sky, for you are capable of achieving anything you set your mind to!",
    "emotions": ["amazed", "joyful", "free", "powerful"]
}
```"""

print("Testing JSON parsing with markdown code blocks...")
print("=" * 60)

# Strip markdown code blocks if present
cleaned_text = response_text.strip()
if '```json' in cleaned_text:
    cleaned_text = re.sub(r'```json\s*', '', cleaned_text)
    cleaned_text = re.sub(r'\s*```', '', cleaned_text)
elif '```' in cleaned_text:
    cleaned_text = re.sub(r'```\s*', '', cleaned_text)

print("\nCleaned text (first 200 chars):")
print(cleaned_text[:200] + "...")

# Try to parse JSON
json_match = re.search(r'{[\s\S]*}', cleaned_text, re.DOTALL)

if json_match:
    json_str = json_match.group(0)
    try:
        response_json = json.loads(json_str)
        print("\n✓ JSON parsed successfully on first try!")
    except json.JSONDecodeError as e:
        print(f"\n✗ First parse failed: {e}")
        print("Trying fixes...")
        try:
            # Use a more aggressive fix for newlines
            # Find all string values and escape their newlines
            def fix_newlines(match):
                value = match.group(1)
                # Escape newlines in the value
                return f'"{value.replace(chr(10), " ")}"'

            fixed_json_str = re.sub(r'"([^"]*)"', fix_newlines, json_str, flags=re.DOTALL)
            response_json = json.loads(fixed_json_str)
            print("✓ JSON parsed after newline fix!")
        except json.JSONDecodeError as e2:
            print(f"✗ Still failed: {e2}")
            response_json = None

    if response_json:
        print(f"\nTitle: {response_json.get('title')}")
        print(f"Interpretation (first 100 chars): {response_json.get('interpretation')[:100]}...")
        print(f"Emotions: {response_json.get('emotions')}")

        # Extract emotions
        emotions_raw = response_json.get("emotions", [])
        if isinstance(emotions_raw, list):
            emotions = [e.strip().lower() for e in emotions_raw if isinstance(e, str)]
            emotions = [e for e in emotions if 3 <= len(e) <= 15 and e.replace(' ', '').isalpha()]
            emotions = emotions[:4]
            print(f"\n✓ Processed emotions: {emotions}")
        else:
            print("\n✗ Emotions not a list")
else:
    print("\n✗ No JSON found in response")
