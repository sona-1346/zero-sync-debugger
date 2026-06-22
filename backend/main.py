import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Database tables
from database.db import Base, engine
from models.bug import Bug  # Import model to register it in Base.metadata
Base.metadata.create_all(bind=engine)

# Import routes
from api.routes import router as api_router

app = FastAPI(
    title="Zero-Sync Debugger API",
    description="Backend API for remembering and resolving developer bugs using SQLite, OpenAI and Parcle API.",
    version="1.0.0"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routes
app.include_router(api_router)

@app.get("/")
def health_check():
    return {
        "status": "online",
        "app": "Zero-Sync Debugger API",
        "tagline": "Debug once. Remember forever."
    }

if __name__ == "__main__":
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
