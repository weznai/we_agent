import json
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, FileResponse
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
    RAGQueryRequest,
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


@router.post("/rag/search")
async def rag_search(
    req: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = knowledge_service.rag_search_with_chunks(
        current_user.id, req.query, req.group_id, req.top_k or 5, db
    )
    return {
        "query": req.query,
        "results": [r.model_dump() for r in results],
        "total": len(results),
    }


@router.post("/rag/answer-stream")
async def rag_answer_stream(
    req: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    search_results = knowledge_service.rag_search_with_chunks(
        current_user.id, req.query, req.group_id, req.top_k or 5, db
    )

    async def event_generator():
        search_data = json.dumps({
            "type": "search_results",
            "results": [r.model_dump() for r in search_results],
            "total": len(search_results),
        }, ensure_ascii=False)
        yield f"data: {search_data}\n\n"

        full_content = ""
        try:
            async for chunk in knowledge_service.rag_answer_stream(
                current_user.id,
                req.query,
                search_results,
                db,
                model_id=req.model_id,
            ):
                full_content += chunk
                data = json.dumps({"type": "chunk", "content": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"[RAG Stream] Error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
            return

        yield f"data: {json.dumps({'type': 'done', 'total_length': len(full_content)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/mineru-image/{filename:path}")
async def get_mineru_image(filename: str):
    from ..config import get_settings
    settings = get_settings()
    mineru_dir = os.path.join(settings.UPLOAD_DIR, "mineru_output")
    if not os.path.exists(mineru_dir):
        raise HTTPException(status_code=404, detail="mineru_output not found")
    for root, dirs, files in os.walk(mineru_dir):
        if filename in files:
            return FileResponse(
                os.path.join(root, filename),
                media_type="image/jpeg",
            )
    raise HTTPException(status_code=404, detail=f"Image not found: {filename}")
