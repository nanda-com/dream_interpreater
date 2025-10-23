"""
Enhanced Error Handling for Dream Explorer
Provides custom exception classes and error handlers.
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from typing import Optional, Dict, Any
import traceback


class DreamExplorerException(Exception):
    """Base exception for Dream Explorer feature."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class EmbeddingGenerationError(DreamExplorerException):
    """Raised when embedding generation fails."""

    def __init__(self, message: str = "Failed to generate embedding", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class VectorSearchError(DreamExplorerException):
    """Raised when vector similarity search fails."""

    def __init__(self, message: str = "Failed to search dreams", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class LLMGenerationError(DreamExplorerException):
    """Raised when LLM response generation fails."""

    def __init__(self, message: str = "Failed to generate AI response", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class DreamNotFoundError(DreamExplorerException):
    """Raised when a dream is not found."""

    def __init__(self, dream_id: int, message: Optional[str] = None):
        super().__init__(
            message=message or f"Dream with ID {dream_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"dream_id": dream_id}
        )


class InsufficientDreamsError(DreamExplorerException):
    """Raised when user doesn't have enough dreams for analysis."""

    def __init__(self, current_count: int, required_count: int = 3):
        super().__init__(
            message=f"You need at least {required_count} dreams for this analysis. You currently have {current_count}.",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"current_count": current_count, "required_count": required_count}
        )


class InvalidQueryError(DreamExplorerException):
    """Raised when query is invalid or too short."""

    def __init__(self, message: str = "Invalid query"):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


async def dream_explorer_exception_handler(request: Request, exc: DreamExplorerException) -> JSONResponse:
    """
    Handle Dream Explorer custom exceptions.

    Args:
        request: The request object
        exc: The exception instance

    Returns:
        JSON response with error details
    """
    logger.error(
        f"Dream Explorer Error: {exc.message} | "
        f"Status: {exc.status_code} | "
        f"Details: {exc.details} | "
        f"Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle generic exceptions with logging.

    Args:
        request: The request object
        exc: The exception instance

    Returns:
        JSON response with error details
    """
    # Log the full traceback
    logger.error(
        f"Unhandled Exception: {str(exc)} | "
        f"Path: {request.url.path} | "
        f"Traceback: {traceback.format_exc()}"
    )

    # Don't expose internal errors to clients in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later.",
            "path": request.url.path
        }
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle validation exceptions with better error messages.

    Args:
        request: The request object
        exc: The exception instance

    Returns:
        JSON response with validation error details
    """
    logger.warning(
        f"Validation Error: {str(exc)} | "
        f"Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Invalid input data",
            "details": str(exc),
            "path": request.url.path
        }
    )


def safe_execute(func, error_class: type = DreamExplorerException, error_message: str = "Operation failed"):
    """
    Decorator to safely execute functions with error handling.

    Args:
        func: Function to wrap
        error_class: Exception class to raise on error
        error_message: Error message to use

    Returns:
        Wrapped function
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except error_class:
            # Re-raise custom exceptions
            raise
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise error_class(
                message=error_message,
                details={"original_error": str(e)}
            )

    return wrapper


class ErrorContext:
    """Context manager for error handling with logging."""

    def __init__(
        self,
        operation: str,
        error_class: type = DreamExplorerException,
        re_raise: bool = True
    ):
        self.operation = operation
        self.error_class = error_class
        self.re_raise = re_raise

    def __enter__(self):
        logger.debug(f"Starting operation: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            logger.debug(f"Completed operation: {self.operation}")
            return True

        logger.error(
            f"Error in operation '{self.operation}': {exc_val} | "
            f"Type: {exc_type.__name__}"
        )

        if self.re_raise:
            if isinstance(exc_val, (DreamExplorerException, HTTPException)):
                # Don't wrap custom exceptions
                return False

            # Wrap generic exceptions
            raise self.error_class(
                message=f"Failed to {self.operation}",
                details={"original_error": str(exc_val)}
            ) from exc_val

        return True  # Suppress exception


def validate_dream_count(dream_count: int, minimum: int = 1) -> None:
    """
    Validate that user has enough dreams.

    Args:
        dream_count: Number of dreams user has
        minimum: Minimum required dreams

    Raises:
        InsufficientDreamsError: If user doesn't have enough dreams
    """
    if dream_count < minimum:
        raise InsufficientDreamsError(
            current_count=dream_count,
            required_count=minimum
        )


def validate_query(query: str, min_length: int = 3, max_length: int = 500) -> None:
    """
    Validate query string.

    Args:
        query: Query string to validate
        min_length: Minimum query length
        max_length: Maximum query length

    Raises:
        InvalidQueryError: If query is invalid
    """
    if not query or not query.strip():
        raise InvalidQueryError("Query cannot be empty")

    if len(query.strip()) < min_length:
        raise InvalidQueryError(
            f"Query must be at least {min_length} characters long"
        )

    if len(query) > max_length:
        raise InvalidQueryError(
            f"Query must not exceed {max_length} characters"
        )
