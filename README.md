# Dream Journal AI 🌙✨

An AI-powered dream journal that helps you record, analyze, and explore your dreams with advanced natural language processing and semantic search.

## 🌐 Quick Links

- [Website](https://dreamidiary.com)
- [Google Playstore](https://play.google.com/store/apps/details?id=com.tinystars.dreamidiary)
- [Frontend Repository](https://github.com/Syamgith/ai-dream-journal-frontend)

<p align="center">
  <img src="pics/ss1.jpg" alt="Login" width="250"/>
  <img src="pics/ss3.jpg" alt="Dream List" width="250"/>
  <img src="pics/ss2.jpg" alt="Add Dream" width="250"/>
</p>

## 🎯 Overview

Dream Journal AI combines cutting-edge AI technology with psychological dream analysis to help users record, interpret, and explore their dreams. Using Google's Gemini AI and vector embeddings, it provides personalized dream insights and pattern discovery.

## ✨ Key Features

### 🤖 AI-Powered Interpretation

- **Smart Dream Analysis**: Google Gemini AI generates personalized dream interpretations
- **Auto-Title Generation**: AI creates meaningful titles for your dreams

### 🔍 Dream Explorer

- **Conversational Interface**: Chat with your dream history using natural language
- **Semantic Search**: Find dreams by meaning, not just keywords (pgvector + sentence transformers)
- **Pattern Analysis**: Discover recurring themes, symbols, and emotions
- **Dream Comparison**: Compare two dreams to find connections and insights
- **Smart Fallback**: 3-level search (semantic → keyword → text) ensures results

### 🔐 Security & Authentication

- JWT-based authentication
- Google OAuth integration
- Secure password hashing with bcrypt

## 🛠 Technology Stack

### Backend

- **Framework**: FastAPI (async/await)
- **AI Models**: Google Gemini (gemini-2.5-flash-lite), LangChain
- **Database**: PostgreSQL with AsyncSQLAlchemy ORM
- **Vector Search**: pgvector extension
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2, 384-dim)
- **Authentication**: JWT + OAuth2 (Google)

### Frontend

- React Native mobile app
- Modern web interface

## 🏗 Architecture

### RAG System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Dream Journal AI - RAG Flow                │
└─────────────────────────────────────────────────────────────────┘

User Query ──► Embedding Model ──► Vector Search ──► Context ──► LLM
                (all-MiniLM-L6)     (pgvector)      (dreams)     (Gemini)
                                                                   │
                                                                   ▼
                                                              AI Response

┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐
│ User Dreams     │      │ PGVector         │      │ Google      │
│ (PostgreSQL)    │◄────►│                  │─────►│ Gemini API  │
└─────────────────┘      └──────────────────┘      └─────────────┘
```

### Database Schema

```
┌──────────────┐         ┌─────────────────┐
│    Users     │         │   DreamEntry    │
├──────────────┤         ├─────────────────┤
│ id (PK)      │────┐    │ id (PK)         │
│ email        │    │    │ user_id (FK)    │◄────┐
│ username     │    └───►│ title           │     │
│ password     │         │ description     │     │
└──────────────┘         │ interpretation  │     │
                         │ emotion_tags    │     │
                         │ timestamp       │     │
                         └─────────────────┘     │
                                  │              │
                                  │              │
                         ┌────────▼────────┐     │
                         │  DreamVector    │     │
                         ├─────────────────┤     │
                         │ id (PK)         │     │
                         │ dream_id (FK)   │─────┘
                         │ user_id (FK)    │
                         │ embedding       │◄─── pgvector (384-dim)
                         │ created_at      │
                         └─────────────────┘
```

### Project Structure

```
src/backend/
├── api/
│   ├── endpoints/
│   │   ├── dreams.py            # Dream CRUD operations
│   │   ├── dream_explorer.py    # Conversational search
│   │   └── users.py             # User management
│   └── routes.py                # Router aggregation
├── services/
│   ├── dream_service.py         # Dream business logic
│   ├── dream_explorer_service.py # Dream history exploration
│   └── dream_retrieval_service.py # Vector search & embeddings
├── models/
│   ├── dreamentry.py            # Dream SQLAlchemy model
│   ├── dream_vector.py          # Embedding storage model
│   ├── user.py                  # User model
│   └── schemas.py               # Pydantic validation schemas
├── ai_interpreters/
│   └── gemini_interpreter.py    # Google Gemini integration
└── utils/
    ├── auth.py                  # JWT authentication
    └── config.py                # Settings management
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+ (with pgvector extension)
- Google Gemini API Key

### Installation

```bash
# Clone and setup
git clone https://github.com/Syamgith/ai-dream-journal.git
cd ai-dream-journal
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment (.env file)
PostgreSQL_URL=postgresql+asyncpg://user:password@localhost:5432/dream_journal
GOOGLE_API_KEY=your_gemini_api_key
JWT_SECRET=your_jwt_secret
LLM_MODEL_NAME=gemini-2.5-flash-lite

# Initialize database
alembic upgrade head

# Run server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Deployment

```bash
docker-compose up --build
```

## 📡 API Documentation

**Interactive Docs**:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Core Endpoints

#### Dreams Management

- `POST /dreams/` - Create dream with AI interpretation
- `GET /dreams/` - List user's dreams
- `GET /dreams/{id}` - Get specific dream
- `PUT /dreams/{id}` - Update dream
- `DELETE /dreams/{id}` - Delete dream

#### Dream Explorer 🔍

- `POST /dream-explorer/ask` - Chat with your dream history

  ```json
  {
    "question": "What do my flying dreams mean?",
    "chat_history": [],
    "top_k": 5
  }
  ```

- `POST /dream-explorer/search` - Semantic search across dreams

  ```json
  {
    "query": "dreams about water and oceans",
    "top_k": 5,
    "emotion_tags": ["calm"]
  }
  ```

- `GET /dream-explorer/similar/{dream_id}` - Find similar dreams

- `POST /dream-explorer/patterns` - Discover recurring patterns

  ```json
  {
    "pattern_query": "recurring nightmares",
    "top_k": 10
  }
  ```

- `POST /dream-explorer/compare` - Compare two dreams
  ```json
  {
    "dream_id_1": 123,
    "dream_id_2": 456
  }
  ```

#### Authentication

- `POST /token` - Login (JWT)
- `POST /users/register` - Register new user
- `POST /auth/google` - Google OAuth

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_dream_explorer_endpoints.py
pytest tests/test_dream_service.py
```

## 🎨 How It Works

1. **Dream Entry**: User creates a dream → AI generates interpretation using Gemini
2. **Embedding Creation**: Dream description → Sentence Transformer → 384-dim vector → Stored in pgvector
3. **Semantic Search**: Query → Embedded → Similarity search in pgvector → Ranked results
4. **Dream Explorer**: Question → Retrieves relevant dreams → LangChain + Gemini → Conversational response
5. **Fallback Search**: Semantic → Keyword matching → Text pattern search (ensures results)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

Built with: **Google Gemini AI** • **FastAPI** • **LangChain** • **pgvector** • **Sentence Transformers**

---

<p align="center">Made with ❤️ for dreamers everywhere</p>
