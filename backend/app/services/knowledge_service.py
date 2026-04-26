import os
import time
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..entities import (
    Knowledge,
    KnowledgeGroup,
    KnowledgeChunk,
    KnowledgeSetting,
    Model,
    Provider,
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
    FileChunksResponse,
    ChunkInfo,
)
from .embedding_service import EmbeddingService, RerankService
from .chunking_service import split_text_to_chunks
from .vector_store_service import VectorStoreService
from ..config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

MAX_FILE_SIZE = 20 * 1024 * 1024

_embedding_service: Optional[EmbeddingService] = None
_rerank_service: Optional[RerankService] = None


def _get_vector_store() -> VectorStoreService:
    return VectorStoreService.get_instance()


def get_embedding_service(db: Session = None, model_id: Optional[int] = None) -> EmbeddingService:
    global _embedding_service

    if db and model_id:
        model = db.query(Model).filter(Model.id == model_id, Model.is_active == True).first()
        if model:
            provider = db.query(Provider).filter(Provider.id == model.provider_id, Provider.is_active == True).first() if model.provider_id else None
            if model.model_path:
                if _embedding_service is None:
                    _embedding_service = EmbeddingService(dimension=model.embedding_dimension or settings.EMBEDDING_DIMENSION)
                if not _embedding_service.is_loaded or _embedding_service.model_info != f"local:{model.model_path}":
                    _embedding_service.load_local_model(model.model_path)
            elif provider and provider.api_base and provider.api_key:
                if _embedding_service is None:
                    _embedding_service = EmbeddingService(dimension=model.embedding_dimension or settings.EMBEDDING_DIMENSION)
                _embedding_service.configure_api(
                    api_base=provider.api_base,
                    api_key=provider.api_key,
                    model=model.name,
                    dimension=model.embedding_dimension or 0,
                )
            return _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService(dimension=settings.EMBEDDING_DIMENSION)
    return _embedding_service


def get_rerank_service(db: Session, model_id: Optional[int] = None) -> Optional[RerankService]:
    global _rerank_service

    if model_id:
        rerank_model = db.query(Model).filter(
            Model.id == model_id,
            Model.model_type == "rerank",
            Model.is_active == True,
        ).first()
    else:
        rerank_model = db.query(Model).filter(
            Model.model_type == "rerank",
            Model.is_active == True,
        ).first()
    if not rerank_model:
        return None

    if _rerank_service is None:
        _rerank_service = RerankService()

    if rerank_model.model_path:
        if not _rerank_service.is_loaded:
            _rerank_service.load_local_model(rerank_model.model_path)
    elif rerank_model.provider_id:
        provider = db.query(Provider).filter(Provider.id == rerank_model.provider_id, Provider.is_active == True).first()
        if provider and provider.api_base and provider.api_key:
            _rerank_service.configure_api(
                api_base=provider.api_base,
                api_key=provider.api_key,
                model=rerank_model.name,
            )
    return _rerank_service


def _extract_text(content_bytes: bytes, ext: str) -> str:
    ext = ext.lower()
    if ext in ("txt", "md", "csv", "json", "py", "js", "html", "css", "xml", "yaml", "yml", "log", "sql", "sh", "bat"):
        try:
            return content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return content_bytes.decode("gbk", errors="ignore")

    if ext == "pdf":
        return _extract_pdf(content_bytes)
    if ext in ("doc", "docx"):
        return _extract_docx(content_bytes, ext)
    if ext in ("xls", "xlsx"):
        return _extract_xlsx(content_bytes)

    try:
        return content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return content_bytes.decode("gbk", errors="ignore")


def _extract_pdf(content_bytes: bytes) -> str:
    try:
        import io
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(content_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        result = "\n\n".join(pages)
        if not result.strip():
            logger.warning(f"[Extract] PDF text is empty after extraction, pages={len(reader.pages)}")
        return result
    except ImportError:
        raise ImportError("PyPDF2 未安装，无法提取 PDF 文本。请执行: pip install PyPDF2")
    except Exception as e:
        logger.error(f"[Extract] PDF extraction failed: {e}", exc_info=True)
        raise RuntimeError(f"PDF 文本提取失败: {e}") from e


def _extract_docx(content_bytes: bytes, ext: str) -> str:
    try:
        import io
        if ext == "docx":
            from docx import Document
            doc = Document(io.BytesIO(content_bytes))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        else:
            return ""
    except ImportError:
        raise ImportError("python-docx 未安装，无法提取 DOCX 文本。请执行: pip install python-docx")
    except Exception as e:
        logger.error(f"[Extract] DOCX extraction failed: {e}", exc_info=True)
        raise RuntimeError(f"DOCX 文本提取失败: {e}") from e


def _extract_xlsx(content_bytes: bytes) -> str:
    try:
        import io
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(content_bytes), read_only=True)
        rows = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                cells = [str(c) if c is not None else "" for c in row]
                if any(cells):
                    rows.append(" | ".join(cells))
        return "\n".join(rows)
    except ImportError:
        raise ImportError("openpyxl 未安装，无法提取 XLSX 文本。请执行: pip install openpyxl")
    except Exception as e:
        logger.error(f"[Extract] XLSX extraction failed: {e}", exc_info=True)
        raise RuntimeError(f"XLSX 文本提取失败: {e}") from e


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
    filename: str,
    content_bytes: bytes,
    db: Session,
    group_id: Optional[int] = None,
) -> KnowledgeResponse:
    start_time = time.time()
    logger.info(
        f"[Knowledge] File upload start: user_id={user_id}, filename={filename}, group_id={group_id}"
    )

    file_size = len(content_bytes)
    if file_size > MAX_FILE_SIZE:
        logger.warning(
            f"[Knowledge] File too large: filename={file.filename}, size={file_size}"
        )
        raise HTTPException(status_code=400, detail="File size exceeds 20MB limit")

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    ext = filename.rsplit(".", 1)[-1] if "." in filename else "txt"
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as f:
        f.write(content_bytes)
    logger.info(f"[Knowledge] File saved: path={file_path}, size={file_size}")

    extract_error = None
    content_text = ""
    try:
        content_text = _extract_text(content_bytes, ext)
        if content_text:
            logger.info(
                f"[Knowledge] Text content extracted: length={len(content_text)}"
            )
    except Exception as e:
        extract_error = str(e)
        logger.error(f"[Knowledge] Text extraction failed: file={filename}, error={e}", exc_info=True)

    item = KnowledgeFactory.create(
        user_id,
        filename,
        group_id=group_id,
        file_path=file_path,
        file_type=ext,
        file_size=file_size,
        content=content_text,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    indexing_error = None
    if content_text:
        logger.info(
            f"[Knowledge] Starting indexing: file_id={item.id}, content_length={len(content_text)}"
        )
        try:
            index_knowledge(item, db)
            db.refresh(item)
        except Exception as e:
            logger.error(f"[Knowledge] Indexing failed: file_id={item.id}, error={e}", exc_info=True)
            indexing_error = str(e)
    elif extract_error:
        logger.info(
            f"[Knowledge] Text extraction failed, skipping indexing: file_id={item.id}"
        )

    elapsed = time.time() - start_time
    logger.info(
        f"[Knowledge] File upload complete: id={item.id}, name={filename}, "
        f"indexed={item.indexed}, chunks={item.chunk_count}, elapsed={elapsed:.2f}s"
    )
    resp = KnowledgeResponse.model_validate(item)
    resp_dict = resp.model_dump()
    if extract_error:
        resp_dict["extract_error"] = extract_error
    if indexing_error:
        resp_dict["indexing_error"] = indexing_error
    return resp_dict


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

    try:
        vs = _get_vector_store()
        vs.delete_by_knowledge_id(item.id)
    except Exception as e:
        logger.warning(f"[Knowledge] VectorStore delete failed: {e}")

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

    try:
        vs = _get_vector_store()
        vs.delete_by_knowledge_id(item.id)
    except Exception as e:
        logger.warning(f"[Knowledge] VectorStore delete failed: {e}")

    if not item.content and item.file_path and os.path.exists(item.file_path):
        logger.info(f"[Knowledge] Content empty, re-extracting from file: {item.file_path}")
        try:
            with open(item.file_path, "rb") as f:
                content_bytes = f.read()
            item.content = _extract_text(content_bytes, item.file_type)
            if item.content:
                logger.info(f"[Knowledge] Re-extracted text: length={len(item.content)}")
                db.commit()
            else:
                logger.warning(f"[Knowledge] Re-extract produced empty text: file_id={file_id}")
        except Exception as e:
            logger.error(f"[Knowledge] Re-extract failed: file_id={file_id}, error={e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"文本提取失败：{e}")

    if item.content:
        try:
            index_knowledge(item, db)
            db.refresh(item)
        except Exception as e:
            logger.error(f"[Knowledge] Reindex failed: file_id={file_id}, error={e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"索引失败：{e}")
        elapsed = time.time() - start_time
        logger.info(
            f"[Knowledge] Reindex complete: file_id={file_id}, chunks={item.chunk_count}, elapsed={elapsed:.2f}s"
        )
        return {"message": "Reindexed", "chunks": item.chunk_count}
    logger.info(
        f"[Knowledge] Reindex skipped (no content): file_id={file_id}"
    )
    return {"message": "No content to index"}


def get_file_chunks(user_id: int, file_id: int, db: Session) -> FileChunksResponse:
    logger.info(f"[Knowledge] Get file chunks: user_id={user_id}, file_id={file_id}")
    item = (
        db.query(Knowledge)
        .filter(Knowledge.id == file_id, Knowledge.user_id == user_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="File not found")

    chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.knowledge_id == item.id)
        .order_by(KnowledgeChunk.chunk_index)
        .all()
    )

    chunk_infos = [
        ChunkInfo(
            chunk_index=c.chunk_index,
            content=c.content,
            char_count=len(c.content),
        )
        for c in chunks
    ]

    return FileChunksResponse(
        file_id=item.id,
        file_name=item.name,
        total_chunks=len(chunk_infos),
        chunks=chunk_infos,
    )


# ── Search ──────────────────────────────────────────────


def search_knowledge(
    user_id: int, query: str, group_id: Optional[int], top_k: int, db: Session
) -> List[KnowledgeSearchResult]:
    start_time = time.time()
    logger.info(
        f"[Knowledge] Search: user_id={user_id}, query_length={len(query)}, group_id={group_id}, top_k={top_k}"
    )

    ks = get_or_create_settings(user_id, db, group_id=group_id)
    emb_svc = get_embedding_service(db=db, model_id=ks.embedding_model_id)
    try:
        query_vec = emb_svc.embed_query(query)
    except Exception as e:
        logger.error(f"[Knowledge] Embedding failed in search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Embedding 生成失败：{e}")

    try:
        vs = _get_vector_store()
        results = vs.search(
            query_embedding=query_vec,
            user_id=user_id,
            group_id=group_id,
            top_k=top_k,
        )
    except Exception as e:
        logger.warning(f"[Knowledge] VectorStore search failed, falling back: {e}")
        return _search_fallback(user_id, query_vec, group_id, top_k, ks, db)

    if not results:
        logger.info("[Knowledge] Search: no results found")
        return []

    knowledge_cache = {}
    scored = []
    for r in results:
        kid = r["metadata"].get("knowledge_id", 0)
        if kid not in knowledge_cache:
            knowledge_cache[kid] = (
                db.query(Knowledge).filter(Knowledge.id == kid).first()
            )
        kn = knowledge_cache.get(kid)
        scored.append(
            KnowledgeSearchResult(
                chunk_id=r["id"],
                knowledge_id=kid,
                knowledge_name=kn.name if kn else "",
                content=r["content"],
                score=r["score"],
                chunk_index=r["metadata"].get("chunk_index", 0),
            )
        )

    if ks.enable_rerank:
        rerank_svc = get_rerank_service(db, model_id=ks.rerank_model_id)
        if rerank_svc and len(scored) > 0:
            candidate_count = min(len(scored), top_k * 3)
            candidates = scored[:candidate_count]
            rerank_results = rerank_svc.rerank(
                query, [c.content for c in candidates], top_k=top_k
            )
            reranked = []
            for rr in rerank_results:
                idx = rr.get("index", 0)
                if idx < len(candidates):
                    item = candidates[idx]
                    item.score = rr.get("score", item.score)
                    reranked.append(item)
            scored = reranked

    elapsed = time.time() - start_time
    logger.info(
        f"[Knowledge] Search complete: results={len(scored[:top_k])}, top_score={scored[0].score if scored else 0:.4f}, elapsed={elapsed:.2f}s"
    )
    return scored[:top_k]


def _search_fallback(user_id, query_vec, group_id, top_k, ks, db):
    q = (
        db.query(KnowledgeChunk)
        .join(Knowledge, KnowledgeChunk.knowledge_id == Knowledge.id)
        .filter(Knowledge.user_id == user_id)
    )
    if group_id is not None:
        q = q.filter(KnowledgeChunk.group_id == group_id)
    chunks = q.all()

    if not chunks:
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
                chunk_id=str(chunk.id),
                knowledge_id=chunk.knowledge_id,
                knowledge_name=knowledge_name.name if knowledge_name else "",
                content=chunk.content,
                score=score,
                chunk_index=chunk.chunk_index,
            )
        )

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]


# ── Settings ───────────────────────────────────────────


def get_or_create_settings(user_id: int, db: Session, group_id: Optional[int] = None) -> KnowledgeSetting:
    q = db.query(KnowledgeSetting).filter(KnowledgeSetting.user_id == user_id)
    if group_id is not None:
        q = q.filter(KnowledgeSetting.group_id == group_id)
    else:
        q = q.filter(KnowledgeSetting.group_id.is_(None))
    ks = q.first()
    if not ks:
        ks = KnowledgeSettingFactory.create(user_id, group_id=group_id)
        db.add(ks)
        db.commit()
        db.refresh(ks)
    return ks


def get_settings_response(user_id: int, db: Session, group_id: Optional[int] = None) -> KnowledgeSettingsResponse:
    ks = get_or_create_settings(user_id, db, group_id=group_id)
    return KnowledgeSettingsResponse.model_validate(ks)


def update_settings(user_id: int, update_data: dict, db: Session) -> KnowledgeSettingsResponse:
    logger.info(f"[Knowledge] Update settings: user_id={user_id}")
    group_id = update_data.pop("group_id", None)
    ks = get_or_create_settings(user_id, db, group_id=group_id)
    for key, value in update_data.items():
        if value is not None:
            setattr(ks, key, value)
    db.commit()
    db.refresh(ks)
    logger.info(f"[Knowledge] Settings updated: user_id={user_id}, group_id={group_id}")
    return KnowledgeSettingsResponse.model_validate(ks)


def list_embedding_models(db: Session):
    models = db.query(Model).filter(
        Model.is_active == True,
        Model.model_type.in_(["embedding", "rerank"]),
    ).order_by(Model.model_type, Model.name).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "display_name": m.display_name or m.name,
            "model_type": m.model_type,
            "model_path": m.model_path or "",
            "embedding_dimension": m.embedding_dimension or 0,
        }
        for m in models
    ]


# ── Recall Test ────────────────────────────────────────


def recall_test(
    user_id: int, query: str, top_k: Optional[int], db: Session, group_id: Optional[int] = None
) -> List[dict]:
    start_time = time.time()
    logger.info(
        f"[Knowledge] Recall test: user_id={user_id}, query_length={len(query)}, top_k={top_k}, group_id={group_id}"
    )

    ks = get_or_create_settings(user_id, db, group_id=group_id)
    top_k = top_k or ks.retrieval_top_k or 5
    emb_svc = get_embedding_service(db=db, model_id=ks.embedding_model_id)
    try:
        query_vec = emb_svc.embed_query(query)
    except Exception as e:
        logger.error(f"[Knowledge] Embedding failed in recall test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Embedding 生成失败：{e}")

    try:
        vs = _get_vector_store()
        results = vs.search(
            query_embedding=query_vec,
            user_id=user_id,
            group_id=group_id,
            top_k=top_k,
        )
    except Exception as e:
        logger.error(f"[Knowledge] VectorStore search failed in recall test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"向量检索失败：{e}")

    knowledge_cache = {}
    scored = []
    for r in results:
        kid = r["metadata"].get("knowledge_id", 0)
        if kid not in knowledge_cache:
            knowledge_cache[kid] = (
                db.query(Knowledge).filter(Knowledge.id == kid).first()
            )
        kn = knowledge_cache.get(kid)
        scored.append(
            {
                "chunk_id": r["id"],
                "knowledge_id": kid,
                "knowledge_name": kn.name if kn else "",
                "content": r["content"],
                "score": r["score"],
                "chunk_index": r["metadata"].get("chunk_index", 0),
                "retrieval_method": ks.retrieval_method,
            }
        )

    if ks.enable_rerank:
        rerank_svc = get_rerank_service(db, model_id=ks.rerank_model_id)
        if rerank_svc and len(scored) > 0:
            candidate_count = min(len(scored), top_k * 3)
            candidates = scored[:candidate_count]
            rerank_results = rerank_svc.rerank(
                query, [c["content"] for c in candidates], top_k=top_k
            )
            reranked = []
            for rr in rerank_results:
                idx = rr.get("index", 0)
                if idx < len(candidates):
                    item = candidates[idx]
                    item["score"] = rr.get("score", item["score"])
                    reranked.append(item)
            scored = reranked

    elapsed = time.time() - start_time
    logger.info(
        f"[Knowledge] Recall test complete: results={len(scored[:top_k])}, top_score={scored[0]['score'] if scored else 0:.4f}, elapsed={elapsed:.2f}s"
    )
    return scored[:top_k]


# ── Indexing ────────────────────────────────────────────


def index_knowledge(item: Knowledge, db: Session):
    start_time = time.time()
    logger.info(
        f"[Knowledge] Indexing: file_id={item.id}, content_length={len(item.content)}"
    )

    ks = db.query(KnowledgeSetting).filter(
        KnowledgeSetting.user_id == item.user_id
    ).first()
    if not ks:
        logger.warning(f"[Knowledge] No settings found for user_id={item.user_id}, using defaults")
    chunk_method = ks.chunk_method if ks else "auto"
    chunk_size = ks.chunk_size if ks else settings.CHUNK_SIZE
    chunk_overlap = ks.chunk_overlap if ks else settings.CHUNK_OVERLAP
    embedding_model_id = ks.embedding_model_id if ks else None

    chunks_info = split_text_to_chunks(
        item.content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        method=chunk_method,
    )
    if not chunks_info:
        logger.warning(f"[Knowledge] No chunks generated: file_id={item.id}, content_length={len(item.content)}, method={chunk_method}, chunk_size={chunk_size}")
        return

    logger.info(f"[Knowledge] Chunks generated: file_id={item.id}, count={len(chunks_info)}")
    emb_svc = get_embedding_service(db=db, model_id=embedding_model_id)
    logger.info(f"[Knowledge] Generating embeddings: chunks={len(chunks_info)}, model_id={embedding_model_id}, emb_svc_type={type(emb_svc).__name__}, is_loaded={emb_svc.is_loaded}")
    texts = [c["content"] for c in chunks_info]
    embeddings = emb_svc.embed_texts(texts)

    chunk_ids = []
    documents = []
    embedding_list = []
    metadatas = []

    for i, (info, vec) in enumerate(zip(chunks_info, embeddings)):
        chunk = KnowledgeFactory.create_chunk(
            knowledge_id=item.id,
            chunk_index=info["chunk_index"],
            content=info["content"],
            embedding="",
            group_id=item.group_id,
        )
        db.add(chunk)

        chunk_id = f"{item.id}_{info['chunk_index']}"
        meta: dict = {
            "user_id": item.user_id,
            "knowledge_id": item.id,
            "chunk_index": info["chunk_index"],
        }
        if item.group_id is not None:
            meta["group_id"] = item.group_id

        chunk_ids.append(chunk_id)
        documents.append(info["content"])
        embedding_list.append(vec)
        metadatas.append(meta)

    try:
        vs = _get_vector_store()
        vs.add_chunks(
            ids=chunk_ids,
            documents=documents,
            embeddings=embedding_list,
            metadatas=metadatas,
        )
    except Exception as e:
        logger.error(f"[Knowledge] VectorStore add failed: {e}")

    item.chunk_count = len(chunks_info)
    item.indexed = True
    db.commit()

    elapsed = time.time() - start_time
    logger.info(
        f"[Knowledge] Indexing complete: file_id={item.id}, chunks={len(chunks_info)}, elapsed={elapsed:.2f}s"
    )


def search_for_agent(user_id: int, query: str, group_id: Optional[int], top_k: int, db: Session) -> List[dict]:
    results = search_knowledge(user_id, query, group_id, top_k, db)
    return [
        {
            "content": r.content,
            "source": r.knowledge_name,
            "score": round(r.score, 4),
            "chunk_index": r.chunk_index,
        }
        for r in results
    ]
