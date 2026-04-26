import os
import time
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

from ..entities import (
    Knowledge,
    KnowledgeGroup,
    KnowledgeChunk,
    KnowledgeSetting,
    Model,
)
from ..entities.factory import (
    KnowledgeGroupFactory,
    KnowledgeFactory,
    KnowledgeSettingFactory,
)
from ..schemas.knowledge import (
    KnowledgeGroupResponse,
    KnowledgeResponse,
    KnowledgeSearchResult,
    KnowledgeSettingsResponse,
    RecallTestResult,
)
from .embedding_service import EmbeddingService
from .chunking_service import split_text_to_chunks
from ..config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

MAX_FILE_SIZE = 20 * 1024 * 1024

_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(dimension=settings.EMBEDDING_DIMENSION)
    return _embedding_service


# ── Groups ──────────────────────────────────────────────


def list_groups(user_id: int, db: Session) -> List[KnowledgeGroupResponse]:
    logger.info(f"[Knowledge] List groups: user_id={user_id}")
    groups = (
        db.query(KnowledgeGroup)
        .filter(KnowledgeGroup.user_id == user_id)
        .order_by(KnowledgeGroup.sort_order, KnowledgeGroup.created_at)
        .all()
    )
    result = []
    for g in groups:
        file_count = (
            db.query(Knowledge)
            .filter(Knowledge.group_id == g.id, Knowledge.user_id == user_id)
            .count()
        )
        resp = KnowledgeGroupResponse.model_validate(g)
        resp.file_count = file_count
        result.append(resp)
    logger.info(f"[Knowledge] Groups returned: user_id={user_id}, count={len(result)}")
    return result


def create_group(
    user_id: int, name: str, description: str = "", color: str = "#6366f1", icon: str = "Folder", db: Session = None
) -> KnowledgeGroupResponse:
    logger.info(f"[Knowledge] Create group: user_id={user_id}, name={name}")
    group = KnowledgeGroupFactory.create(
        user_id, name, description=description, color=color, icon=icon
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    resp = KnowledgeGroupResponse.model_validate(group)
    resp.file_count = 0
    logger.info(f"[Knowledge] Group created: id={group.id}, name={name}")
    return resp


def update_group(
    user_id: int, group_id: int, update_data: dict, db: Session
) -> KnowledgeGroupResponse:
    logger.info(f"[Knowledge] Update group: user_id={user_id}, group_id={group_id}")
    group = (
        db.query(KnowledgeGroup)
        .filter(KnowledgeGroup.id == group_id, KnowledgeGroup.user_id == user_id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    for key, value in update_data.items():
        if value is not None:
            setattr(group, key, value)
    db.commit()
    db.refresh(group)
    file_count = db.query(Knowledge).filter(Knowledge.group_id == group.id).count()
    resp = KnowledgeGroupResponse.model_validate(group)
    resp.file_count = file_count
    logger.info(f"[Knowledge] Group updated: id={group_id}")
    return resp


def delete_group(user_id: int, group_id: int, db: Session):
    logger.info(f"[Knowledge] Delete group: user_id={user_id}, group_id={group_id}")
    group = (
        db.query(KnowledgeGroup)
        .filter(KnowledgeGroup.id == group_id, KnowledgeGroup.user_id == user_id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    files = db.query(Knowledge).filter(Knowledge.group_id == group_id).all()
    for f in files:
        f.group_id = None
    db.delete(group)
    db.commit()
    logger.info(
        f"[Knowledge] Group deleted: id={group_id}, orphaned_files={len(files)}"
    )
    return {"message": "Group deleted"}


# ── Files ───────────────────────────────────────────────


def list_files(
    user_id: int, group_id: Optional[int], db: Session
) -> List[KnowledgeResponse]:
    logger.info(f"[Knowledge] List files: user_id={user_id}, group_id={group_id}")
    q = db.query(Knowledge).filter(Knowledge.user_id == user_id)
    if group_id is not None:
        q = q.filter(Knowledge.group_id == group_id)
    files = q.order_by(Knowledge.created_at.desc()).all()
    logger.info(f"[Knowledge] Files returned: count={len(files)}")
    return [KnowledgeResponse.model_validate(k) for k in files]


def create_file_entry(
    user_id: int, name: str, db: Session, **kwargs
) -> KnowledgeResponse:
    logger.info(f"[Knowledge] Create file entry: user_id={user_id}, name={name}")
    if kwargs.get("group_id"):
        grp = (
            db.query(KnowledgeGroup)
            .filter(
                KnowledgeGroup.id == kwargs["group_id"],
                KnowledgeGroup.user_id == user_id,
            )
            .first()
        )
        if not grp:
            raise HTTPException(status_code=404, detail="Group not found")
    item = KnowledgeFactory.create(user_id, name, **kwargs)
    db.add(item)
    db.commit()
    db.refresh(item)
    logger.info(f"[Knowledge] File entry created: id={item.id}, name={name}")
    return KnowledgeResponse.model_validate(item)


def upload_file(
    user_id: int,
    file: UploadFile,
    db: Session,
    group_id: Optional[int] = None,
) -> KnowledgeResponse:
    start_time = time.time()
    logger.info(
        f"[Knowledge] File upload start: user_id={user_id}, filename={file.filename}, group_id={group_id}"
    )

    content_bytes = file.read()
    file_size = len(content_bytes)
    if file_size > MAX_FILE_SIZE:
        logger.warning(
            f"[Knowledge] File too large: filename={file.filename}, size={file_size}"
        )
        raise HTTPException(status_code=400, detail="File size exceeds 20MB limit")

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "txt"
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as f:
        f.write(content_bytes)
    logger.info(f"[Knowledge] File saved: path={file_path}, size={file_size}")

    content_text = ""
    if ext.lower() in (
        "txt",
        "md",
        "csv",
        "json",
        "py",
        "js",
        "html",
        "css",
        "xml",
        "yaml",
        "yml",
        "log",
        "sql",
        "sh",
        "bat",
    ):
        try:
            content_text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content_text = content_bytes.decode("gbk", errors="ignore")
        logger.info(
            f"[Knowledge] Text content extracted: length={len(content_text)}"
        )

    item = KnowledgeFactory.create(
        user_id,
        file.filename,
        group_id=group_id,
        file_path=file_path,
        file_type=ext,
        file_size=file_size,
        content=content_text,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    if content_text:
        logger.info(
            f"[Knowledge] Starting indexing: file_id={item.id}, content_length={len(content_text)}"
        )
        index_knowledge(item, db)
    else:
        logger.info(
            f"[Knowledge] No text content, skipping indexing: file_id={item.id}"
        )

    elapsed = time.time() - start_time
    logger.info(
        f"[Knowledge] File upload complete: id={item.id}, name={file.filename}, elapsed={elapsed:.2f}s"
    )
    return KnowledgeResponse.model_validate(item)


def update_file(
    user_id: int, file_id: int, update_data: dict, db: Session
) -> KnowledgeResponse:
    logger.info(f"[Knowledge] Update file: user_id={user_id}, file_id={file_id}")
    item = (
        db.query(Knowledge)
        .filter(Knowledge.id == file_id, Knowledge.user_id == user_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    for key, value in update_data.items():
        if value is not None:
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    logger.info(f"[Knowledge] File updated: id={file_id}")
    return KnowledgeResponse.model_validate(item)


def delete_file(user_id: int, file_id: int, db: Session):
    logger.info(f"[Knowledge] Delete file: user_id={user_id}, file_id={file_id}")
    item = (
        db.query(Knowledge)
        .filter(Knowledge.id == file_id, Knowledge.user_id == user_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    chunk_count = (
        db.query(KnowledgeChunk).filter(KnowledgeChunk.knowledge_id == item.id).count()
    )
    db.query(KnowledgeChunk).filter(KnowledgeChunk.knowledge_id == item.id).delete()
    if item.file_path and os.path.exists(item.file_path):
        os.remove(item.file_path)
    db.delete(item)
    db.commit()
    logger.info(
        f"[Knowledge] File deleted: id={file_id}, removed_chunks={chunk_count}"
    )
    return {"message": "File deleted"}


def reindex_file(user_id: int, file_id: int, db: Session):
    start_time = time.time()
    logger.info(f"[Knowledge] Reindex file: user_id={user_id}, file_id={file_id}")
    item = (
        db.query(Knowledge)
        .filter(Knowledge.id == file_id, Knowledge.user_id == user_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    db.query(KnowledgeChunk).filter(KnowledgeChunk.knowledge_id == item.id).delete()
    db.commit()
    if item.content:
        index_knowledge(item, db)
        elapsed = time.time() - start_time
        logger.info(
            f"[Knowledge] Reindex complete: file_id={file_id}, chunks={item.chunk_count}, elapsed={elapsed:.2f}s"
        )
        return {"message": "Reindexed", "chunks": item.chunk_count}
    logger.info(
        f"[Knowledge] Reindex skipped (no content): file_id={file_id}"
    )
    return {"message": "No content to index"}


# ── Search ──────────────────────────────────────────────


def search_knowledge(
    user_id: int, query: str, group_id: Optional[int], top_k: int, db: Session
) -> List[KnowledgeSearchResult]:
    start_time = time.time()
    logger.info(
        f"[Knowledge] Search: user_id={user_id}, query_length={len(query)}, group_id={group_id}, top_k={top_k}"
    )

    emb_svc = get_embedding_service()
    query_vec = emb_svc.embed_query(query)

    q = (
        db.query(KnowledgeChunk)
        .join(Knowledge, KnowledgeChunk.knowledge_id == Knowledge.id)
        .filter(Knowledge.user_id == user_id)
    )
    if group_id is not None:
        q = q.filter(KnowledgeChunk.group_id == group_id)
    chunks = q.all()

    if not chunks:
        logger.info("[Knowledge] Search: no chunks found")
        return []

    scored = []
    for chunk in chunks:
        if not chunk.embedding:
            continue
        vec = EmbeddingService.deserialize_embedding(chunk.embedding)
        score = EmbeddingService.cosine_similarity(query_vec, vec)
        knowledge_name = (
            db.query(Knowledge).filter(Knowledge.id == chunk.knowledge_id).first()
        )
        scored.append(
            KnowledgeSearchResult(
                chunk_id=chunk.id,
                knowledge_id=chunk.knowledge_id,
                knowledge_name=knowledge_name.name if knowledge_name else "",
                content=chunk.content,
                score=score,
                chunk_index=chunk.chunk_index,
            )
        )

    scored.sort(key=lambda x: x.score, reverse=True)
    elapsed = time.time() - start_time
    logger.info(
        f"[Knowledge] Search complete: total_chunks={len(chunks)}, results={len(scored[:top_k])}, top_score={scored[0].score if scored else 0:.4f}, elapsed={elapsed:.2f}s"
    )
    return scored[:top_k]


# ── Settings ───────────────────────────────────────────


def get_or_create_settings(user_id: int, db: Session) -> KnowledgeSetting:
    ks = (
        db.query(KnowledgeSetting)
        .filter(KnowledgeSetting.user_id == user_id)
        .first()
    )
    if not ks:
        ks = KnowledgeSettingFactory.create(user_id)
        db.add(ks)
        db.commit()
        db.refresh(ks)
    return ks


def get_settings_response(user_id: int, db: Session) -> KnowledgeSettingsResponse:
    ks = get_or_create_settings(user_id, db)
    return KnowledgeSettingsResponse.model_validate(ks)


def update_settings(user_id: int, update_data: dict, db: Session) -> KnowledgeSettingsResponse:
    logger.info(f"[Knowledge] Update settings: user_id={user_id}")
    ks = get_or_create_settings(user_id, db)
    for key, value in update_data.items():
        if value is not None:
            setattr(ks, key, value)
    db.commit()
    db.refresh(ks)
    logger.info(f"[Knowledge] Settings updated: user_id={user_id}")
    return KnowledgeSettingsResponse.model_validate(ks)


def list_embedding_models(db: Session):
    models = db.query(Model).filter(Model.is_active == True, Model.model_type == "embedding").all()
    return [{"id": m.id, "name": m.name, "display_name": m.display_name or m.name} for m in models]


# ── Recall Test ────────────────────────────────────────


def recall_test(
    user_id: int, query: str, top_k: Optional[int], db: Session
) -> List[dict]:
    start_time = time.time()
    logger.info(
        f"[Knowledge] Recall test: user_id={user_id}, query_length={len(query)}, top_k={top_k}"
    )

    ks = get_or_create_settings(user_id, db)
    top_k = top_k or ks.retrieval_top_k or 5
    emb_svc = get_embedding_service()
    query_vec = emb_svc.embed_query(query)

    chunks = (
        db.query(KnowledgeChunk)
        .join(Knowledge, KnowledgeChunk.knowledge_id == Knowledge.id)
        .filter(Knowledge.user_id == user_id)
        .all()
    )

    if not chunks:
        logger.info("[Knowledge] Recall test: no chunks found")
        return []

    scored = []
    for chunk in chunks:
        if not chunk.embedding:
            continue
        vec = EmbeddingService.deserialize_embedding(chunk.embedding)
        score = EmbeddingService.cosine_similarity(query_vec, vec)
        knowledge_obj = (
            db.query(Knowledge).filter(Knowledge.id == chunk.knowledge_id).first()
        )
        scored.append(
            {
                "chunk_id": chunk.id,
                "knowledge_id": chunk.knowledge_id,
                "knowledge_name": knowledge_obj.name if knowledge_obj else "",
                "content": chunk.content,
                "score": score,
                "chunk_index": chunk.chunk_index,
                "retrieval_method": ks.retrieval_method,
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    elapsed = time.time() - start_time
    logger.info(
        f"[Knowledge] Recall test complete: total_chunks={len(chunks)}, results={len(scored[:top_k])}, top_score={scored[0]['score'] if scored else 0:.4f}, elapsed={elapsed:.2f}s"
    )
    return scored[:top_k]


# ── Indexing ────────────────────────────────────────────


def index_knowledge(item: Knowledge, db: Session):
    start_time = time.time()
    logger.info(
        f"[Knowledge] Indexing: file_id={item.id}, content_length={len(item.content)}"
    )

    chunks_text = split_text_to_chunks(item.content)
    if not chunks_text:
        logger.info(f"[Knowledge] No chunks generated: file_id={item.id}")
        return

    emb_svc = get_embedding_service()
    logger.info(f"[Knowledge] Generating embeddings: chunks={len(chunks_text)}")
    embeddings = emb_svc.embed_texts(chunks_text)

    from ..entities.factory import KnowledgeFactory

    for i, (text, vec) in enumerate(zip(chunks_text, embeddings)):
        chunk = KnowledgeFactory.create_chunk(
            knowledge_id=item.id,
            chunk_index=i,
            content=text,
            embedding=EmbeddingService.serialize_embedding(vec),
            group_id=item.group_id,
        )
        db.add(chunk)

    item.chunk_count = len(chunks_text)
    item.indexed = True
    db.commit()

    elapsed = time.time() - start_time
    logger.info(
        f"[Knowledge] Indexing complete: file_id={item.id}, chunks={len(chunks_text)}, elapsed={elapsed:.2f}s"
    )
