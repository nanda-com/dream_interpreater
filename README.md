# Dream Journal AI

## Overview

An AI-powered dream interpretation API using Google Gemini and FastAPI.

## Features

- Dream entry creation
- AI-powered dream interpretation
- RESTful API endpoints

## Setup

### Prerequisites

- Python 3.10+
- Google Gemini API Key

### Installation

1. Clone the repository
2. Create a virtual environment

```bash
python -m venv venv # to create venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

##Test API
curl -X POST "http://127.0.0.1:8000/dreams/" \
 -H "accept: application/json" \
 -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDIzMDM0MjQsInN1YiI6IjQiLCJ0eXBlIjoiYWNjZXNzIn0.loz-WryhvQq-oOBKUVNwiWoCwtxZK3yCnIpWnLmYoUE" \
 -H "Content-Type: application/json" \
 -d '{
"title": "string",
"description": "I saw an apple flying while I was walking in the park.",
"date": "2025-03-16T08:57:23.323Z",
"emotions": ["string"],
"tags": ["string"]
}'

##

curl -X 'GET' \
 'http://127.0.0.1:8000/dreams/' \
 -H 'accept: application/json' \
 -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDIzMDM0MjQsInN1YiI6IjQiLCJ0eXBlIjoiYWNjZXNzIn0.loz-WryhvQq-oOBKUVNwiWoCwtxZK3yCnIpWnLmYoUE"
