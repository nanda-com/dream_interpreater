# src/backend/ai_interpreters/gemini_interpreter.py

import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional
from src.backend.services.dream_rag_service import DreamRAGService

# Load environment variables from .env file
load_dotenv()

class GeminiDreamInterpreter:
    def __init__(self, api_key: Optional[str] = None):
        # Directly get the API key from environment variables
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        
        # Validate API key
        if not self.api_key:
            raise ValueError(
                "No Google API Key found. "
                "Please set GOOGLE_API_KEY in your .env file."
            )
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.rag_service = DreamRAGService()

    def interpret_dream(self, description: str, title: Optional[str] = None) -> tuple[str, str]:
        try:
            prompt = f"""
            You are a creative dream interpreter. Given the dream description below, provide an interpretation that is fun and insightful. Avoid emojis. 
            Return your response in this exact JSON format without any additional text:
            {{
            "title": A catchy, meaningful title that captures the essence of the dream with exactly 2 words,
            "interpretation": A creative and entertaining interpretation of the dream that identifies key symbols and offers positive insights or reflections. Keep the tone light and enjoyable while addressing the main elements of the dream. Make it two paragraph and format curretly.
            }}

            Dream description: {description}""" if (title is None) else f"""
            You are a creative dream interpreter. Given the dream description below, provide an interpretation that is fun and insightful. Avoid emojis. 
            Return your response in this exact JSON format without any additional text:
            {{
            "interpretation": A creative and entertaining interpretation of the dream that identifies key symbols and offers positive insights or reflections. Keep the tone light and enjoyable while addressing the main elements of the dream. Make it two paragraph and format curretly.
            }}
            Dream description: {description}"""
            # Augment prompt with RAG context
            # augmented_prompt = self.rag_service.augment_prompt(description)
            augmented_prompt = prompt
            # Generate interpretation
            print("augmented promnt : \n" + augmented_prompt)
            response = self.model.generate_content(augmented_prompt)
            
            # Extract interpretation and title from the response
            response_text = response.text.strip()
            
            try:
                import json
                import re
                
                # Try to extract JSON content using regex in case there's text before or after the JSON
                json_match = re.search(r'{[\s\S]*}', response_text)
                if json_match:
                    json_str = json_match.group(0)
                    
                    # Try to handle cases where single quotes might be used instead of double quotes
                    # or where there might be escaped quotes
                    try:
                        response_json = json.loads(json_str)
                    except json.JSONDecodeError:
                        # Try replacing single quotes with double quotes for JSON keys and string values
                        # This is a simple fix for common LLM formatting issues
                        fixed_json_str = re.sub(r"'([^']+)':", r'"\1":', json_str)  # Fix keys
                        fixed_json_str = re.sub(r':\s*\'([^\']+)\'', r': "\1"', fixed_json_str)  # Fix values
                        try:
                            response_json = json.loads(fixed_json_str)
                        except json.JSONDecodeError:
                            # If that still fails, try a more aggressive conversion (use with caution)
                            import ast
                            try:
                                # Use ast.literal_eval to parse Python dict syntax
                                response_dict = ast.literal_eval(json_str)
                                response_json = response_dict
                            except (SyntaxError, ValueError):
                                raise json.JSONDecodeError("Failed to parse JSON with alternative methods", json_str, 0)
                else:
                    # If no JSON pattern found, try parsing the whole response
                    response_json = json.loads(response_text)
                
                interpretation = response_json.get("interpretation", "Unable to extract interpretation")
                title = response_json.get("title") if title is None else title
            except (json.JSONDecodeError, AttributeError) as e:
                # Handle case where response is not valid JSON
                print(f"Error parsing JSON from response: {response_text}")
                print(f"Error details: {str(e)}")
                
                # Last resort: try to extract key parts using regex
                if not title and title is None:
                    title_match = re.search(r'"title":\s*"([^"]+)"', response_text)
                    if title_match:
                        title = title_match.group(1)
                    else:
                        title = "Unable to get title"
                
                interp_match = re.search(r'"interpretation":\s*"([^"]+)"', response_text)
                if interp_match:
                    interpretation = interp_match.group(1)
                else:
                    interpretation = "Unable to parse interpretation"
            
            print("title: " + (title if title else "None"))
            print("interpretation: " + interpretation)
            return interpretation, title

        except Exception as e:
            print(f"Error in dream interpretation: {e}")
            return f"An error occurred during interpretation: {str(e)}", title or "Dream"

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