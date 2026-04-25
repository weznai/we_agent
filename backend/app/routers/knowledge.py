import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.knowledge import Knowledge
from ..models.knowledge_group import KnowledgeGroup
from ..models.knowledge_chunk import KnowledgeChunk
from ..models.user import User
from ..schemas.knowledge import (
    KnowledgeGroupCreate, KnowledgeGroupUpdate, KnowledgeGroupResponse,
    KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse,
    KnowledgeSearchRequest, KnowledgeSearchResult,
)
from ..utils.auth import get_current_user
from ..utils.embedding import EmbeddingService
from ..utils.chunking import split_text_to_chunks
from ..config import get_settings

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

settings = get_settings()
embedding_svc = EmbeddingService(dimension=settings.EMBEDDING_DIMENSION)

MAX_FILE_SIZE = 20 * 1024 * 1024


# ── Groups ──────────────────────────────────────────────

@router.get("/groups", response_model=List[KnowledgeGroupResponse])
async def list_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    groups = db.query(KnowledgeGroup).filter(
        KnowledgeGroup.user_id == current_user.id
    ).order_by(KnowledgeGroup.sort_order, KnowledgeGroup.created_at).all()

    result = []
    for g in groups:
        file_count = db.query(Knowledge).filter(
            Knowledge.group_id == g.id, Knowledge.user_id == current_user.id
        ).count()
        resp = KnowledgeGroupResponse.model_validate(g)
        resp.file_count = file_count
        result.append(resp)
    return result


@router.post("/groups", response_model=KnowledgeGroupResponse)
async def create_group(
    data: KnowledgeGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = KnowledgeGroup(user_id=current_user.id, **data.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    resp = KnowledgeGroupResponse.model_validate(group)
    resp.file_count = 0
    return resp


@router.put("/groups/{group_id}", response_model=KnowledgeGroupResponse)
async def update_group(
    group_id: int,
    data: KnowledgeGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = db.query(KnowledgeGroup).filter(
        KnowledgeGroup.id == group_id, KnowledgeGroup.user_id == current_user.id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(group, key, value)
    db.commit()
    db.refresh(group)
    file_count = db.query(Knowledge).filter(Knowledge.group_id == group.id).count()
    resp = KnowledgeGroupResponse.model_validate(group)
    resp.file_count = file_count
    return resp


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = db.query(KnowledgeGroup).filter(
        KnowledgeGroup.id == group_id, KnowledgeGroup.user_id == current_user.id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    files = db.query(Knowledge).filter(Knowledge.group_id == group_id).all()
    for f in files:
        f.group_id = None
    db.delete(group)
    db.commit()
    return {"message": "Group deleted"}


# ── Files ───────────────────────────────────────────────

@router.get("/files", response_model=List[KnowledgeResponse])
async def list_files(
    group_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Knowledge).filter(Knowledge.user_id == current_user.id)
    if group_id is not None:
        q = q.filter(Knowledge.group_id == group_id)
    return [KnowledgeResponse.model_validate(k) for k in q.order_by(Knowledge.created_at.desc()).all()]


@router.post("/files", response_model=KnowledgeResponse)
async def create_file_entry(
    data: KnowledgeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.group_id:
        grp = db.query(KnowledgeGroup).filter(
            KnowledgeGroup.id == data.group_id, KnowledgeGroup.user_id == current_user.id
        ).first()
        if not grp:
            raise HTTPException(status_code=404, detail="Group not found")
    item = Knowledge(user_id=current_user.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return KnowledgeResponse.model_validate(item)


@router.post("/files/upload", response_model=KnowledgeResponse)
async def upload_file(
    file: UploadFile = File(...),
    group_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content_bytes = await file.read()
    file_size = len(content_bytes)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 20MB limit")

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "txt"
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    content_text = ""
    if ext.lower() in ("txt", "md", "csv", "json", "py", "js", "html", "css", "xml", "yaml", "yml", "log", "sql", "sh", "bat"):
        try:
            content_text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content_text = content_bytes.decode("gbk", errors="ignore")

    item = Knowledge(
        user_id=current_user.id,
        group_id=group_id,
        name=file.filename,
        file_path=file_path,
        file_type=ext,
        file_size=file_size,
        content=content_text,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    if content_text:
        _index_knowledge(item, db)

    return KnowledgeResponse.model_validate(item)


@router.put("/files/{file_id}", response_model=KnowledgeResponse)
async def update_file(
    file_id: int,
    data: KnowledgeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(Knowledge).filter(
        Knowledge.id == file_id, Knowledge.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return KnowledgeResponse.model_validate(item)


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(Knowledge).filter(
        Knowledge.id == file_id, Knowledge.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="File not found")

    db.query(KnowledgeChunk).filter(KnowledgeChunk.knowledge_id == item.id).delete()
    if item.file_path and os.path.exists(item.file_path):
        os.remove(item.file_path)
    db.delete(item)
    db.commit()
    return {"message": "File deleted"}


@router.post("/files/{file_id}/reindex")
async def reindex_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(Knowledge).filter(
        Knowledge.id == file_id, Knowledge.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    db.query(KnowledgeChunk).filter(KnowledgeChunk.knowledge_id == item.id).delete()
    db.commit()
    if item.content:
        _index_knowledge(item, db)
        return {"message": "Reindexed", "chunks": item.chunk_count}
    return {"message": "No content to index"}


# ── Search ──────────────────────────────────────────────

@router.post("/search", response_model=List[KnowledgeSearchResult])
async def search_knowledge(
    req: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query_vec = embedding_svc.embed_query(req.query)

    q = db.query(KnowledgeChunk).join(
        Knowledge, KnowledgeChunk.knowledge_id == Knowledge.id
    ).filter(Knowledge.user_id == current_user.id)

    if req.group_id is not None:
        q = q.filter(KnowledgeChunk.group_id == req.group_id)

    chunks = q.all()
    if not chunks:
        return []

    scored = []
    for chunk in chunks:
        if not chunk.embedding:
            continue
        vec = EmbeddingService.deserialize_embedding(chunk.embedding)
        score = EmbeddingService.cosine_similarity(query_vec, vec)
        knowledge_name = db.query(Knowledge).filter(Knowledge.id == chunk.knowledge_id).first()
        scored.append(KnowledgeSearchResult(
            chunk_id=chunk.id,
            knowledge_id=chunk.knowledge_id,
            knowledge_name=knowledge_name.name if knowledge_name else "",
            content=chunk.content,
            score=score,
            chunk_index=chunk.chunk_index,
        ))

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:req.top_k]


# ── Helpers ─────────────────────────────────────────────

def _index_knowledge(item: Knowledge, db: Session):
    chunks_text = split_text_to_chunks(item.content)
    if not chunks_text:
        return

    embeddings = embedding_svc.embed_texts(chunks_text)

    for i, (text, vec) in enumerate(zip(chunks_text, embeddings)):
        chunk = KnowledgeChunk(
            knowledge_id=item.id,
            group_id=item.group_id,
            chunk_index=i,
            content=text,
            embedding=EmbeddingService.serialize_embedding(vec),
        )
        db.add(chunk)

    item.chunk_count = len(chunks_text)
    item.indexed = True
    db.commit()
