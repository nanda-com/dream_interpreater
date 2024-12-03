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
        self.model = genai.GenerativeModel('gemini-pro')
        self.rag_service = DreamRAGService()

    def interpret_dream(self, description: str) -> str:
        try:
            # Craft a detailed prompt for dream interpretation
            prompt = f"""
            You are an expert dream psychologist. Provide a deep, insightful, and compassionate 
            interpretation of the following dream description. Include:
            1. Possible symbolic meanings
            2. Potential psychological insights
            3. Emotional undertones
            4. Constructive reflections

            Dream Description:
            {description}

            Interpretation:
            """

            # Augment prompt with RAG context
            augmented_prompt = self.rag_service.augment_prompt(description)
            # Generate interpretation
            response = self.model.generate_content(augmented_prompt)
            # response = augmented_prompt
            print("hi from interpret dream")
            
            # Return the text response, handling potential errors
            # return response
            return response.text.strip() or "Unable to generate interpretation"

        except Exception as e:
            print(f"Error in dream interpretation: {e}")
            return f"An error occurred during interpretation: {str(e)}"

    def generate_dream_title(self, description: str) -> Optional[str]:
        """
        Generate a creative, evocative title for the dream
        """
        try:
            prompt = f"""
            Create a unique, poetic, and intriguing title for this dream description:
            {description}

            Title should be:
            - Concise (5-7 words)
            - Metaphorical
            - Capture the dream's essence
            """

            response = self.model.generate_content(prompt)
            return response.text.strip() or None

        except Exception as e:
            print(f"Error generating dream title: {e}")
            return None