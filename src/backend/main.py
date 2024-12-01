# src/backend/main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, DreamEntry
from ai_services import DreamAIService

app = FastAPI()
ai_service = DreamAIService()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/dream/")
def create_dream_entry(
    description: str, 
    db: Session = Depends(get_db)
):
    # Generate AI interpretation
    interpretation = ai_service.generate_interpretation(description)
    
    # Generate dream image
    dream_image = ai_service.generate_dream_image(interpretation)
    
    # Save to database
    new_entry = DreamEntry(
        description=description,
        interpretation=interpretation,
        image_url=f"uploads/{uuid.uuid4()}.png"
    )
    db.add(new_entry)
    db.commit()
    
    return {
        "interpretation": interpretation,
        "image_url": new_entry.image_url
    }