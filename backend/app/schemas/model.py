from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ModelCreate(BaseModel):
    provider_id: Optional[int] = None
    name: str
    display_name: Optional[str] = ""
    model_type: Optional[str] = "chat"
    description: Optional[str] = ""
    max_tokens: Optional[int] = None
    temperature: Optional[str] = "0.7"
    embedding_dimension: Optional[int] = 0
    model_path: Optional[str] = ""


class ModelUpdate(BaseModel):
    provider_id: Optional[int] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
    model_type: Optional[str] = None
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[str] = None
    is_active: Optional[bool] = None
    embedding_dimension: Optional[int] = None
    model_path: Optional[str] = None


class ModelResponse(BaseModel):
    id: int
    provider_id: Optional[int] = None
    name: str
    display_name: str
    model_type: str
    description: str
    max_tokens: Optional[int] = None
    temperature: str
    is_active: bool
    embedding_dimension: int
    model_path: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
