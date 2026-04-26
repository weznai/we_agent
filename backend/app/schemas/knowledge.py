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
    chunk_id: str
    knowledge_id: int
    knowledge_name: str
    content: str
    score: float
    chunk_index: int


class KnowledgeSettingsUpdate(BaseModel):
    group_id: Optional[int] = None
    embedding_model_id: Optional[int] = None
    enable_rerank: Optional[bool] = None
    rerank_model_id: Optional[int] = None
    chunk_method: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    retrieval_method: Optional[str] = None
    retrieval_top_k: Optional[int] = None
    score_threshold: Optional[str] = None


class KnowledgeSettingsResponse(BaseModel):
    id: int
    user_id: int
    group_id: Optional[int] = None
    embedding_model_id: Optional[int] = None
    enable_rerank: bool
    rerank_model_id: Optional[int] = None
    chunk_method: str
    chunk_size: int
    chunk_overlap: int
    retrieval_method: str
    retrieval_top_k: int
    score_threshold: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecallTestRequest(BaseModel):
    query: str
    group_id: Optional[int] = None
    top_k: Optional[int] = 5


class RecallTestResult(BaseModel):
    chunk_id: str
    knowledge_id: int
    knowledge_name: str
    content: str
    score: float
    chunk_index: int
    retrieval_method: str


class ChunkInfo(BaseModel):
    chunk_index: int
    content: str
    char_count: int


class FileChunksResponse(BaseModel):
    file_id: int
    file_name: str
    total_chunks: int
    chunks: List[ChunkInfo]
