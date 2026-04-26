import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..entities import User
from ..dependencies import get_current_user
from ..schemas.knowledge import (
    KnowledgeGroupCreate,
    KnowledgeGroupUpdate,
    KnowledgeGroupResponse,
    KnowledgeCreate,
    KnowledgeUpdate,
    KnowledgeResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
    KnowledgeSettingsUpdate,
    KnowledgeSettingsResponse,
    RecallTestRequest,
    RecallTestResult,
    FileChunksResponse,
)
from ..services import knowledge_service
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


# ── Groups ──────────────────────────────────────────────


@router.get("/groups", response_model=List[KnowledgeGroupResponse])
async def list_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.list_groups(current_user.id, db)


@router.post("/groups", response_model=KnowledgeGroupResponse)
async def create_group(
    data: KnowledgeGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.create_group(
        current_user.id, data.name, data.description, data.color, data.icon, db=db
    )


@router.put("/groups/{group_id}", response_model=KnowledgeGroupResponse)
async def update_group(
    group_id: int,
    data: KnowledgeGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.update_group(
        current_user.id, group_id, data.model_dump(exclude_unset=True), db
    )


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.delete_group(current_user.id, group_id, db)


# ── Files ───────────────────────────────────────────────


@router.get("/files", response_model=List[KnowledgeResponse])
async def list_files(
    group_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.list_files(current_user.id, group_id, db)


@router.post("/files", response_model=KnowledgeResponse)
async def create_file_entry(
    data: KnowledgeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.create_file_entry(
        current_user.id, data.name, db,
        description=data.description, group_id=data.group_id,
    )


@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    group_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content_bytes = await file.read()
    return knowledge_service.upload_file(
        current_user.id, file.filename, content_bytes, db, group_id=group_id
    )


@router.put("/files/{file_id}", response_model=KnowledgeResponse)
async def update_file(
    file_id: int,
    data: KnowledgeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.update_file(
        current_user.id, file_id, data.model_dump(exclude_unset=True), db
    )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.delete_file(current_user.id, file_id, db)


@router.post("/files/{file_id}/reindex")
async def reindex_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.reindex_file(current_user.id, file_id, db)


@router.get("/files/{file_id}/chunks", response_model=FileChunksResponse)
async def get_file_chunks(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.get_file_chunks(current_user.id, file_id, db)


# ── Search ──────────────────────────────────────────────


@router.post("/search", response_model=List[KnowledgeSearchResult])
async def search_knowledge(
    req: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.search_knowledge(
        current_user.id, req.query, req.group_id, req.top_k, db
    )


# ── Settings ───────────────────────────────────────────


@router.get("/settings", response_model=KnowledgeSettingsResponse)
async def get_settings(
    group_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.get_settings_response(current_user.id, db, group_id=group_id)


@router.put("/settings", response_model=KnowledgeSettingsResponse)
async def update_settings(
    data: KnowledgeSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.update_settings(
        current_user.id, data.model_dump(exclude_unset=True), db
    )


@router.get("/embedding-models")
async def list_embedding_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.list_embedding_models(db)


# ── Recall Test ────────────────────────────────────────


@router.post("/recall-test", response_model=List[RecallTestResult])
async def recall_test(
    req: RecallTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_service.recall_test(current_user.id, req.query, req.top_k, db, group_id=req.group_id)
