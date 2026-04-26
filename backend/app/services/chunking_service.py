import re
from typing import List, Dict, Any

from ..config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


def split_text_to_chunks(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
    method: str = "auto",
) -> List[Dict[str, Any]]:
    settings = get_settings()
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if not text or not text.strip():
        return []

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if method == "sentence":
        chunks_text = _split_by_sentence(text, chunk_size, chunk_overlap)
    elif method == "paragraph":
        chunks_text = _split_by_paragraph(text, chunk_size, chunk_overlap)
    elif method == "fixed":
        chunks_text = _split_fixed(text, chunk_size, chunk_overlap)
    else:
        chunks_text = _split_auto(text, chunk_size, chunk_overlap)

    result = []
    for i, content in enumerate(chunks_text):
        result.append(
            {
                "chunk_index": i,
                "content": content,
                "char_count": len(content),
            }
        )

    logger.info(
        f"[Chunking] Split text: method={method}, chunk_size={chunk_size}, "
        f"overlap={chunk_overlap}, chunks={len(result)}, text_length={len(text)}"
    )
    return result


def _split_auto(text: str, chunk_size: int, overlap: int) -> List[str]:
    paragraphs = _split_into_paragraphs(text)
    if len(paragraphs) <= 1:
        return _split_by_sentence(text, chunk_size, overlap)

    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = (current + "\n\n" + para).strip() if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) <= chunk_size:
                current = para
            else:
                sub_chunks = _split_by_sentence(para, chunk_size, overlap)
                if sub_chunks:
                    for sc in sub_chunks[:-1]:
                        chunks.append(sc)
                    current = sub_chunks[-1] if sub_chunks else ""
                else:
                    current = para[:chunk_size]
            if overlap > 0 and chunks and current:
                overlap_text = chunks[-1][-overlap:]
                current = overlap_text + current

    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]


def _split_by_paragraph(text: str, chunk_size: int, overlap: int) -> List[str]:
    paragraphs = _split_into_paragraphs(text)
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = (current + "\n\n" + para).strip() if current else para
        else:
            if current:
                chunks.append(current)
            current = para
            if overlap > 0 and chunks:
                overlap_text = chunks[-1][-overlap:]
                current = overlap_text + "\n" + current

    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]


def _split_by_sentence(text: str, chunk_size: int, overlap: int) -> List[str]:
    sentences = _split_into_sentences(text)
    chunks = []
    current = ""

    for sent in sentences:
        if len(current) + len(sent) + 1 <= chunk_size:
            current = (current + " " + sent).strip() if current else sent
        else:
            if current:
                chunks.append(current)
            if len(sent) > chunk_size:
                for sub in _split_fixed(sent, chunk_size, 0):
                    chunks.append(sub)
                current = ""
            else:
                current = sent
            if overlap > 0 and chunks and current:
                overlap_text = chunks[-1][-overlap:]
                current = overlap_text + " " + current

    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]


def _split_fixed(text: str, chunk_size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap if end < len(text) else end
    return chunks


def _split_into_paragraphs(text: str) -> List[str]:
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def _split_into_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[。！？.!?\n])\s*", text)
    return [p.strip() for p in parts if p.strip()]
