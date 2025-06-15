# Dream Journal AI

## Quick Links

- 🌐 [Website](https://dreamidiary.com)
- 📱 [Google Playstore Link](https://play.google.com/store/apps/details?id=com.tinystars.dreamidiary)
- 💻 [Frontend Repository](https://github.com/Syamgith/ai-dream-journal-frontend)

### Screenshots

#### Mobile App

<p align="center">
  <img src="pics/ss1.jpg" alt="Login" width="250"/>
  <img src="pics/ss3.jpg" alt="Dream List" width="250"/>
  <img src="pics/ss2.jpg" alt="Add Dream" width="250"/>
</p>

## Overview

Dream Journal AI is an advanced application that leverages artificial intelligence to help users record, analyze, and interpret their dreams. Using Google's Gemini AI model and modern web technologies, it provides intelligent dream interpretation and a seamless user experience.

## Features

- 📝 Dream entry creation and management
- 🤖 AI-powered dream interpretation using Google Gemini
- 🔐 Secure user authentication
- 📱 RESTful API architecture
- 📚 Knowledge base integration for enhanced interpretations

## Technology Stack

### Backend

- **Framework**: FastAPI
- **Server**: Uvicorn
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with OAuth2
- **AI Integration**: Google Gemini, LangChain
- **Vector Database**: FAISS for similarity search

### Frontend

- Modern web interface (details to be added)

## Architecture

### Project Structure

```
├── main.py                 # Application entry point
├── server/                 # Server-side code
│   ├── controllers/        # API controllers
│   └── models/            # Data models
├── app/                   # Frontend application
├── tests/                 # Test files
├── alembic/              # Database migrations
├── types/                # Type definitions
└── dream_knowledge_base/ # Knowledge base for dream interpretation
```

### Database Schema

The application uses PostgreSQL with the following main entities:

- Users
- Dreams
- Interpretations
- Tags
- Emotions

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 12 or higher
- Google Gemini API Key
- Docker (optional, for containerized deployment)

## Installation

### Local Development Setup

1. Clone the repository:

```bash
git clone https://github.com/Syamgith/ai-dream-journal.git
cd ai-dream-journal
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dream_journal
GOOGLE_API_KEY=your_gemini_api_key
SECRET_KEY=your_jwt_secret_key
```

5. Initialize the database:

```bash
alembic upgrade head
```

6. Run the application:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Deployment

1. Build and run using Docker Compose:

```bash
docker-compose up --build
```

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Example API Usage

1. Create a new dream entry:

```bash
curl -X POST "http://localhost:8000/dreams/" \
 -H "accept: application/json" \
 -H "Authorization: Bearer YOUR_JWT_TOKEN" \
 -H "Content-Type: application/json" \
 -d '{
   "title": "Flying Apple",
   "description": "I saw an apple flying while I was walking in the park.",
   "date": "2024-03-16T08:57:23.323Z",
   "emotions": ["amazed", "curious"],
   "tags": ["flying", "fruit", "park"]
}'
```

2. Retrieve dreams:

```bash
curl -X GET "http://localhost:8000/dreams/" \
 -H "accept: application/json" \
 -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Testing

Run the test suite:

```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS protection
- Environment variable configuration
- Input validation with Pydantic

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Gemini AI
- FastAPI
- SQLAlchemy
- LangChain
- All other open-source contributors
