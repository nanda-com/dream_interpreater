# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dream Journal AI is a FastAPI backend application that uses Google Gemini AI to interpret dreams. It features:
- AI-powered dream interpretation using Google Gemini (currently using gemini-2.5-flash-lite)
- PostgreSQL database with async SQLAlchemy ORM
- JWT authentication with OAuth2 (including Google OAuth)
- RESTful API architecture

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Development server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production (Docker)
docker-compose up --build
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py
pytest tests/test_user_endpoints.py
pytest tests/test_dream_service.py
```

### Database Migrations
```bash
# Run migrations
alembic upgrade head
```

## Architecture

### Directory Structure
```
src/backend/
├── api/
│   ├── endpoints/      # API route handlers (dreams.py, users.py, feedback.py, interpretations.py)
│   └── routes.py       # Main router aggregation
├── models/             # SQLAlchemy models and Pydantic schemas
│   ├── user.py
│   ├── dreamentry.py
│   ├── reported_dream.py
│   ├── feedback.py
│   └── schemas.py      # Pydantic validation schemas
├── services/           # Business logic layer
│   ├── dream_service.py      # Dream creation and management
│   └── feedback_service.py
├── ai_interpreters/    # AI integration modules
│   ├── gemini_interpreter.py   # Primary interpreter (Google Gemini)
│   ├── openai_interpreter.py
│   └── huggingface.py
├── utils/
│   ├── auth.py         # JWT authentication utilities
│   ├── config.py       # Settings management with Pydantic
│   └── oauth/
│       └── google.py   # Google OAuth integration
└── databases.py        # Database engine and session management
```

### Request Flow
1. **API Request** → `main.py` (FastAPI app) → `src/backend/api/routes.py`
2. **Routing** → Specific endpoint in `src/backend/api/endpoints/`
3. **Business Logic** → Service layer in `src/backend/services/`
4. **AI Processing** → `GeminiDreamInterpreter`
5. **Database** → Async SQLAlchemy session via `get_db()` dependency
6. **Response** → Pydantic schema validation → JSON response

### Key Components

#### AI Interpretation Pipeline
- **Primary**: `GeminiDreamInterpreter` uses Google Gemini API with configurable model name
- **Model Selection**: Set via `LLM_MODEL_NAME` env var (defaults to 'gemini-2.5-flash-lite')
- The interpreter returns both title and interpretation as a tuple
- Strict output formatting to avoid special characters (no double quotes, slashes)

#### Database Layer
- **Engine**: Async PostgreSQL via asyncpg driver
- **Connection**: Configured via `PostgreSQL_URL` environment variable
- **Pool Settings**: 20 connections, max overflow 10, 30s timeout
- **Session Management**: `get_db()` dependency yields async sessions with proper error handling
- **Auto-initialization**: `create_tables()` checks for existing tables before creation

#### Authentication
- **JWT**: Token-based auth with `OAuth2PasswordBearer`
- **Google OAuth**: Integrated via `src/backend/utils/oauth/google.py`
- **Token URL**: `/token` endpoint
- **Authorization**: Persist in Swagger UI with `persistAuthorization: True`

## Environment Variables

Required variables in `.env`:
```
# Application
APP_NAME=DreamJournalAI
APP_ENV=development
LOG_LEVEL=INFO

# Database
PostgreSQL_URL=postgresql+asyncpg://user:password@host:port/database

# AI Services
GOOGLE_API_KEY=your_gemini_api_key
LLM_MODEL_NAME=gemini-2.5-flash-lite  # Optional, defaults to this
OPENAI_API_KEY=your_openai_key        # Optional, legacy

# Authentication
JWT_SECRET=your_jwt_secret
GOOGLE_CLIENT_ID=your_google_client_id
```

## Coding Guidelines (from rules.md)

When making changes:
- Write minimum code required
- No sweeping changes or unrelated edits
- Focus on the specific task at hand
- Make code precise, modular, and testable
- Don't break existing functionality
- **IMPORTANT**: Log all changes in `ai_changes_log.md` with date, time, file name, and description

## API Documentation

When running, access interactive docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Important Implementation Notes

1. **Dream Creation Flow**: When creating a dream, if no title is provided, the AI generates one. Titles are limited to 35 characters.

2. **Error Handling**: Database errors are caught and mapped to appropriate HTTP exceptions in `databases.py:get_db()`

3. **CORS**: Currently configured for `allow_origins=["*"]` in development (main.py:26)

4. **Model Configuration**: Settings use Pydantic v2 with `model_config` and `SettingsConfigDict` (not the old `Config` class)
