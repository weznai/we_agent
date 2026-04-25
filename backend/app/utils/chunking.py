from typing import List
from ..config import get_settings


def split_text_to_chunks(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[str]:
    settings = get_settings()
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if not text or not text.strip():
        return []

    paragraphs = text.replace("\r\n", "\n").replace("\r", "\n").split("\n\n")
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(para) <= chunk_size:
                current_chunk = para
            else:
                sentences = _split_sentences(para)
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= chunk_size:
                        if current_chunk:
                            current_chunk += " " + sent
                        else:
                            current_chunk = sent
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sent[:chunk_size]
        if chunk_overlap > 0 and chunks and current_chunk:
            overlap_text = chunks[-1][-chunk_overlap:]
            current_chunk = overlap_text + " " + current_chunk

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _split_sentences(text: str) -> List[str]:
    import re
    parts = re.split(r'(?<=[。！？.!?\n])', text)
    return [p.strip() for p in parts if p.strip()]
