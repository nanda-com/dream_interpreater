"""
Dream Explorer Service
Provides conversational interface to explore dream history using RAG with LangChain.
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from src.backend.services.dream_retrieval_service import get_retrieval_service
from src.backend.models.dreamentry import DreamEntry
from src.backend.utils.error_handlers import (
    LLMGenerationError,
    DreamNotFoundError,
    validate_query,
    ErrorContext
)


# Prompt template for dream exploration
DREAM_EXPLORER_PROMPT_TEMPLATE = """You are a helpful dream analyst AI with access to the user's personal dream journal.

Based on these relevant dreams from their history:
{context}

Conversation History:
{chat_history}

User Question: {question}

Provide a thoughtful analysis that:
1. References specific dreams from their history with dates
2. Identifies patterns or recurring themes
3. Offers personalized insights based on their unique dream experiences
4. Keeps the tone warm and supportive
5. If no relevant dreams are found, acknowledge this and provide general guidance

Answer:"""


class DreamExplorerService:
    """Service for conversational exploration of dream history."""

    def __init__(self):
        """Initialize the Dream Explorer service."""
        self.retrieval_service = get_retrieval_service()

        # Initialize Gemini LLM
        model_name = os.getenv("LLM_MODEL_NAME", "gemini-2.0-flash-exp")
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        logger.info(f"Initializing Dream Explorer with model: {model_name}")

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )

        # Create prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["context", "chat_history", "question"],
            template=DREAM_EXPLORER_PROMPT_TEMPLATE
        )

        # Create LLM chain
        self.chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt_template
        )

    def format_dream_context(
        self,
        dreams: List[tuple[DreamEntry, float]]
    ) -> str:
        """
        Format retrieved dreams into context for the LLM.

        Args:
            dreams: List of tuples (DreamEntry, similarity_score)

        Returns:
            Formatted context string
        """
        if not dreams:
            return "No relevant dreams found in the user's history."

        context_parts = []
        for i, (dream, score) in enumerate(dreams, 1):
            date_str = dream.timestamp.strftime("%Y-%m-%d") if dream.timestamp else "Unknown date"

            dream_text = f"""
Dream {i} (Date: {date_str}, Relevance: {score:.2f}):
Title: {dream.title or 'Untitled'}
Description: {dream.description}
Interpretation: {dream.interpretation or 'No interpretation'}
"""
            if dream.emotion_tags:
                dream_text += f"Emotions: {dream.emotion_tags}\n"

            context_parts.append(dream_text)

        return "\n".join(context_parts)

    def format_chat_history(
        self,
        chat_history: List[Dict[str, str]]
    ) -> str:
        """
        Format chat history for the prompt.

        Args:
            chat_history: List of chat messages

        Returns:
            Formatted chat history string
        """
        if not chat_history:
            return "No previous conversation."

        history_parts = []
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_parts.append(f"{role.capitalize()}: {content}")

        return "\n".join(history_parts)

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

        Args:
            db: Database session
            user_id: ID of the user
            question: The user's question
            chat_history: Previous conversation messages
            top_k: Number of dreams to retrieve

        Returns:
            Dictionary with answer, relevant dreams, and updated chat history

        Raises:
            LLMGenerationError: If AI response generation fails
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
                # For meta-questions, retrieve ALL recent dreams (or more dreams)
                logger.info(f"Detected meta-question, retrieving all recent dreams")
                with ErrorContext("retrieve all recent dreams"):
                    # Get all dreams for the user, ordered by recency
                    from sqlalchemy import select
                    result = await db.execute(
                        select(DreamEntry)
                        .where(DreamEntry.user_id == user_id)
                        .order_by(DreamEntry.timestamp.desc())
                        .limit(top_k or 20)  # Get more dreams for pattern analysis
                    )
                    dreams = result.scalars().all()
                    # Convert to same format as semantic search (dream, score)
                    similar_dreams = [(dream, 1.0) for dream in dreams]
            else:
                # For specific questions, use semantic search
                with ErrorContext("retrieve relevant dreams"):
                    similar_dreams = await self.retrieval_service.search_similar_dreams(
                        db=db,
                        user_id=user_id,
                        query=question,
                        top_k=top_k
                    )

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
            # Re-raise custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error in ask_question: {str(e)}")
            raise LLMGenerationError(
                message="An unexpected error occurred while processing your question",
                details={"error": str(e)}
            )

    async def find_patterns(
        self,
        db: AsyncSession,
        user_id: int,
        pattern_query: str,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Find patterns in the user's dream history.

        Args:
            db: Database session
            user_id: ID of the user
            pattern_query: Description of the pattern to find
            top_k: Number of dreams to analyze

        Returns:
            Dictionary with pattern analysis and relevant dreams
        """
        try:
            # Retrieve relevant dreams
            similar_dreams = await self.retrieval_service.search_similar_dreams(
                db=db,
                user_id=user_id,
                query=pattern_query,
                top_k=top_k or 10  # Use more dreams for pattern analysis
            )

            # Create a pattern analysis prompt
            context = self.format_dream_context(similar_dreams)
            pattern_prompt = f"""Analyze these dreams for patterns related to: {pattern_query}

{context}

Provide:
1. Common themes and symbols
2. Recurring emotions or situations
3. Timeline of pattern evolution
4. Psychological insights"""

            # Generate analysis
            response = await self.llm.apredict(pattern_prompt)

            # Format dream summaries
            dream_summaries = [
                {
                    "dream_id": dream.id,
                    "title": dream.title or "Untitled",
                    "date": dream.timestamp.isoformat() if dream.timestamp else None,
                    "relevance_score": float(score)
                }
                for dream, score in similar_dreams
            ]

            return {
                "pattern_analysis": response,
                "relevant_dreams": dream_summaries
            }

        except Exception as e:
            logger.error(f"Error in find_patterns: {str(e)}")
            raise

    async def compare_dreams(
        self,
        db: AsyncSession,
        dream_id_1: int,
        dream_id_2: int,
        user_id: int
    ) -> str:
        """
        Compare two dreams and provide insights.

        Args:
            db: Database session
            dream_id_1: ID of first dream
            dream_id_2: ID of second dream
            user_id: ID of the user

        Returns:
            Comparison analysis
        """
        try:
            from sqlalchemy import select

            # Fetch both dreams
            result = await db.execute(
                select(DreamEntry)
                .where(DreamEntry.id.in_([dream_id_1, dream_id_2]))
                .where(DreamEntry.user_id == user_id)
            )
            dreams = result.scalars().all()

            if len(dreams) != 2:
                raise ValueError("Could not find both dreams")

            # Create comparison prompt
            dream1, dream2 = dreams
            comparison_prompt = f"""Compare these two dreams:

Dream 1 (Date: {dream1.timestamp.strftime('%Y-%m-%d')}):
Title: {dream1.title}
Description: {dream1.description}
Interpretation: {dream1.interpretation}

Dream 2 (Date: {dream2.timestamp.strftime('%Y-%m-%d')}):
Title: {dream2.title}
Description: {dream2.description}
Interpretation: {dream2.interpretation}

Provide:
1. Similarities in themes, symbols, or emotions
2. Key differences
3. Possible connections or evolution between the dreams
4. Insights about what these dreams might reveal together"""

            # Generate comparison
            response = await self.llm.apredict(comparison_prompt)

            return response

        except Exception as e:
            logger.error(f"Error in compare_dreams: {str(e)}")
            raise


# Singleton instance
_explorer_service: Optional[DreamExplorerService] = None


def get_explorer_service() -> DreamExplorerService:
    """
    Get or create singleton explorer service instance.

    Returns:
        DreamExplorerService instance
    """
    global _explorer_service
    if _explorer_service is None:
        _explorer_service = DreamExplorerService()
    return _explorer_service
