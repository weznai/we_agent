from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ModelMappingCreate(BaseModel):
    agent_type: str
    model_id: int
    priority: Optional[int] = 0


class ModelMappingUpdate(BaseModel):
    agent_type: Optional[str] = None
    model_id: Optional[int] = None
    priority: Optional[int] = None


class ModelMappingResponse(BaseModel):
    id: int
    agent_type: str
    model_id: int
    priority: int
    created_at: Optional[datetime] = None
    model_name: Optional[str] = None
    provider_name: Optional[str] = None

    class Config:
        from_attributes = True
