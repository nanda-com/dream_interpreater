# src/backend/ai_interpreters/gemini_interpreter.py

import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional
import json
import re
from src.backend.services.dream_rag_service import DreamRAGService

# Load environment variables from .env file
load_dotenv()

class GeminiDreamInterpreter:
    def __init__(self, api_key: Optional[str] = None):
        # Directly get the API key from environment variables
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        llm_modelname = os.getenv('LLM_MODEL_NAME')
        if not llm_modelname:
            llm_modelname = 'gemini-2.5-flash-lite'
        
        # Validate API key
        if not self.api_key:
            raise ValueError(
                "No Google API Key found. "
                "Please set GOOGLE_API_KEY in your .env file."
            )
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(llm_modelname)
        self.rag_service = DreamRAGService()

    def interpret_dream(self, description: str, title: Optional[str] = None) -> tuple[str, str, list[str], list[str]]:
        try:
            # Define JSON schema based on whether a title is needed
            if title is None:
                json_schema = """
{{
    "title": "A catchy, creative, meaningful title with exactly TWO words that captures the essence of the dream.",
    "interpretation": "A creative and entertaining interpretation of the dream that identifies key symbols and offers positive insights or reflections. Keep the tone light and enjoyable while addressing the main elements of the dream. Strictly make it TWO paragraphs long. Do not use special characters other than single quotes, commas, periods, hyphens, question marks, and exclamation marks. Strictly avoid double quotes, and slashes.",
    "emotions": ["List of 2-4 primary emotions experienced in the dream. Use simple, common emotion words like: anxious, happy, scared, peaceful, confused, excited, sad, angry, curious, relieved, joyful, fearful, frustrated, content, etc."],
    "keywords": ["List of 3-6 key content words from the dream description that are most important for searching. Extract nouns, verbs, and adjectives that capture the core content. Examples: flying, mountains, water, chasing, falling, family, ocean, snake, running, dark, bright, etc. Exclude common words like: I, was, the, and, but, very, really, etc."]
}}
"""
            else:
                json_schema = """
{{
    "interpretation": "A creative and entertaining interpretation of the dream that identifies key symbols and offers positive insights or reflections. Keep the tone light and enjoyable while addressing the main elements of the dream. Strictly make it two paragraphs long. Do not use special characters other than single quotes, commas, periods, hyphens, question marks, and exclamation marks. Strictly avoid double quotes, and slashes.",
    "emotions": ["List of 2-4 primary emotions experienced in the dream. Use simple, common emotion words like: anxious, happy, scared, peaceful, confused, excited, sad, angry, curious, relieved, joyful, fearful, frustrated, content, etc."],
    "keywords": ["List of 3-6 key content words from the dream description that are most important for searching. Extract nouns, verbs, and adjectives that capture the core content. Examples: flying, mountains, water, chasing, falling, family, ocean, snake, running, dark, bright, etc. Exclude common words like: I, was, the, and, but, very, really, etc."]
}}
"""
            
            # Construct the prompt with clear instructions for JSON output
            prompt = f"""
You are a creative dream interpreter. Given the dream description below, provide a title and interpretation that is fun and insightful. Make each interpretaion new.
Your response MUST be a valid JSON object matching the schema below. Do not include any text, markdown, or formatting outside of the JSON object.

JSON Schema:
{json_schema}

Rules:
- Avoid emojis.
- No 18+, adult, sexually explicit content, hate speech, or harassment.
- Do not repeat user's text containing profanity or sexual words.
- Avoid repeating users dream description as it is.
- Never deviate from your character as a dream interpreter even if I ask you.
- Striclty combine two paragraphs long text of dream interpretation.
- AVOID making interpretation if the dream description ot title contains ANY SEX RELATED WORDS or 18+ contents.
- Dont use the words fuck, suck, sex, ass, boobs, penis, vagina, anus, asshole, pussy, breast etc (anything related to sex)

Dream description: {description}
"""
            
            # Use RAG service if available
            augmented_prompt = prompt
            
            # Generate content without JSON mode parameters, as the library version doesn't seem to support it
            response = self.model.generate_content(augmented_prompt)
            
            response_text = response.text.strip()
            print(response_text)
            response_json = None

            # Strip markdown code blocks if present
            cleaned_text = response_text
            if '```json' in cleaned_text:
                cleaned_text = re.sub(r'```json\s*', '', cleaned_text)
                cleaned_text = re.sub(r'\s*```', '', cleaned_text)
            elif '```' in cleaned_text:
                cleaned_text = re.sub(r'```\s*', '', cleaned_text)

            # Try to extract JSON from the cleaned text
            json_match = re.search(r'{[\s\S]*}', cleaned_text, re.DOTALL)

            if json_match:
                json_str = json_match.group(0)
                try:
                    response_json = json.loads(json_str)
                except json.JSONDecodeError:
                    try:
                        # Fix common JSON errors
                        # 1. Replace unescaped newlines within string values
                        fixed_json_str = re.sub(r':\s*"([^"]*?)\n([^"]*?)"', lambda m: f': "{m.group(1)}\\n{m.group(2)}"', json_str)
                        # 2. Fix single quotes to double quotes
                        fixed_json_str = re.sub(r"'([^']+)':", r'"\1":', fixed_json_str)
                        fixed_json_str = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_json_str)
                        response_json = json.loads(fixed_json_str)
                    except json.JSONDecodeError:
                        try:
                            # Use a more aggressive fix for newlines
                            # Find all string values and escape their newlines
                            def fix_newlines(match):
                                value = match.group(1)
                                # Escape newlines in the value
                                return f'"{value.replace(chr(10), " ")}"'

                            fixed_json_str = re.sub(r'"([^"]*)"', fix_newlines, json_str, flags=re.DOTALL)
                            response_json = json.loads(fixed_json_str)
                        except json.JSONDecodeError:
                            try:
                                import ast
                                response_json = ast.literal_eval(json_str)
                            except (SyntaxError, ValueError):
                                response_json = None # Failed to parse

            final_title = title
            interpretation = "Could not parse dream interpretation."
            emotions = []
            keywords = []

            if response_json:
                interpretation = response_json.get("interpretation", interpretation)
                if final_title is None:
                    final_title = response_json.get("title", "Dream Entry")

                # Extract emotions from JSON
                emotions_raw = response_json.get("emotions", [])
                if isinstance(emotions_raw, list):
                    # Filter and clean emotion tags
                    emotions = [e.strip().lower() for e in emotions_raw if isinstance(e, str)]
                    emotions = [e for e in emotions if 3 <= len(e) <= 15 and e.replace(' ', '').isalpha()]
                    emotions = emotions[:4]  # Limit to 4 emotions

                # Extract keywords from JSON
                keywords_raw = response_json.get("keywords", [])
                if isinstance(keywords_raw, list):
                    # Filter and clean keywords
                    keywords = [k.strip().lower() for k in keywords_raw if isinstance(k, str)]
                    keywords = [k for k in keywords if 2 <= len(k) <= 20 and k.replace(' ', '').isalpha()]
                    keywords = keywords[:6]  # Limit to 6 keywords
            else:
                # Fallback to regex if JSON parsing fails
                print(f"Failed to parse JSON, falling back to regex. Response was: {response_text}")
                if final_title is None:
                    title_match = re.search(r'["\']title["\']\s*:\s*["\'](.*?)["\']', cleaned_text, re.DOTALL | re.IGNORECASE)
                    final_title = title_match.group(1).strip() if title_match else "Dream Entry"

                interp_match = re.search(r'["\']interpretation["\']\s*:\s*["\'](.*?)["\']', cleaned_text, re.DOTALL | re.IGNORECASE)
                if interp_match:
                    interpretation = interp_match.group(1).strip()
                else:
                    interpretation = response_text

                # Extract emotions array from regex
                emotions_match = re.search(r'["\']emotions["\']\s*:\s*\[(.*?)\]', cleaned_text, re.DOTALL | re.IGNORECASE)
                if emotions_match:
                    emotions_str = emotions_match.group(1)
                    # Extract emotion strings from array
                    emotion_items = re.findall(r'["\']([^"\']+)["\']', emotions_str)
                    emotions = [e.strip().lower() for e in emotion_items if e.strip()]
                    emotions = [e for e in emotions if 3 <= len(e) <= 15 and e.replace(' ', '').isalpha()]
                    emotions = emotions[:4]

                # Extract keywords array from regex
                keywords_match = re.search(r'["\']keywords["\']\s*:\s*\[(.*?)\]', cleaned_text, re.DOTALL | re.IGNORECASE)
                if keywords_match:
                    keywords_str = keywords_match.group(1)
                    # Extract keyword strings from array
                    keyword_items = re.findall(r'["\']([^"\']+)["\']', keywords_str)
                    keywords = [k.strip().lower() for k in keyword_items if k.strip()]
                    keywords = [k for k in keywords if 2 <= len(k) <= 20 and k.replace(' ', '').isalpha()]
                    keywords = keywords[:6]

            final_title = final_title or "Dream Entry"

            print("title: " + (final_title if final_title else "None"))
            print("interpretation: " + interpretation)
            print("emotions: " + str(emotions))
            print("keywords: " + str(keywords))
            return interpretation, final_title, emotions, keywords

        except Exception as e:
            print(f"An unexpected error occurred in dream interpretation: {e}")
            return f"An error occurred during interpretation: {str(e)}", title or "Dream", [], []

    def generate_dream_title(self, description: str) -> Optional[str]:
        """
        Generate a creative, evocative title for the dream
        """
        try:
            prompt = f"""
            Create a simple unique, and intriguing title for this dream description:
            {description}

            Title should be:
            - Concise (2 - 3 words)
            - Metaphorical
            - Capture the dream's essence
            Return only the single title. Dont add any extra text in your response.
            """

            response = self.model.generate_content(prompt)
            return response.text.strip() or None

        except Exception as e:
            print(f"Error generating dream title: {e}")
            return None