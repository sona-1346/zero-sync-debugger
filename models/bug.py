from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, DateTime
from database.db import Base

# SQLAlchemy Database Model
class Bug(Base):
    __tablename__ = "bugs"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True, nullable=True, default="Default Project")
    error_message = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # JSON serialized embedding float array
    timestamp = Column(DateTime, default=datetime.utcnow)

# Pydantic Schemas for Requests/Responses
class BugBase(BaseModel):
    project_name: Optional[str] = "Default Project"
    error_message: str
    root_cause: str
    solution: str

class BugCreate(BugBase):
    pass

class BugResponse(BugBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class BugSubmitRequest(BaseModel):
    error_message: str
    description: Optional[str] = ""
    project_name: Optional[str] = "Default Project"
    log_content: Optional[str] = ""

class BugAnalysisResponse(BaseModel):
    root_cause: str
    solution: str
    prevention_tips: str
    suggested_commands: str
    suggested_code_changes: str
    suggested_dependency_fixes: str
    similarity_matched: bool = False
    similarity_score: float = 0.0

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    project_name: Optional[str] = "Default Project"

class ChatResponse(BaseModel):
    response: str
