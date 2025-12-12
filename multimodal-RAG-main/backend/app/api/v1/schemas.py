from pydantic import BaseModel, Field
from typing import List, Dict, Any
from backend.app.services.vector_db import KBType

# --- User and Token Schemas ---

class UserBase(BaseModel):
    email: str

class User(UserBase):
    full_name: str | None = None
    disabled: bool | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class HealthCheck(BaseModel):
    """Response model for the health check endpoint."""
    message: str
    google_api_key_loaded: bool

class EmbeddingResponse(BaseModel):
    """Response model for the embedding creation endpoint."""
    status: str
    vector_id: str
    kb_type: KBType
    context_id: str | None

class ExtractionResponse(BaseModel):
    """Response model for the document extraction endpoint."""
    filename: str
    text_length: int
    image_count: int

class RetrievedContext(BaseModel):
    """Represents a single piece of retrieved context from the vector database."""
    id: str
    score: float = Field(..., description="The similarity score of the retrieved item.")
    metadata: Dict[str, Any]

class QueryResponse(BaseModel):
    """Response model for the main RAG query endpoint."""
    query: str
    answer: str
    retrieved_context: List[RetrievedContext]

    class Config:
        # This allows the model to be created from arbitrary class instances
        from_attributes = True