from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class KnowledgeGroupCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    color: Optional[str] = "#6366f1"
    icon: Optional[str] = "Folder"


class KnowledgeGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None


class KnowledgeGroupResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: str
    color: str
    icon: str
    sort_order: int
    file_count: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KnowledgeCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    group_id: Optional[int] = None


class KnowledgeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    group_id: Optional[int] = None
    status: Optional[str] = None


class KnowledgeResponse(BaseModel):
    id: int
    user_id: int
    group_id: Optional[int] = None
    name: str
    description: str
    file_path: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    indexed: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KnowledgeSearchRequest(BaseModel):
    query: str
    group_id: Optional[int] = None
    top_k: Optional[int] = 5


class KnowledgeSearchResult(BaseModel):
    chunk_id: int
    knowledge_id: int
    knowledge_name: str
    content: str
    score: float
    chunk_index: int
