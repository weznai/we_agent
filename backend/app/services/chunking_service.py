import re
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

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


def split_mineru_content_list(
    content_list: List[Dict[str, Any]],
    output_dir: str,
    document_name: str = "doc",
    max_chunk_size: int = 1000,
    min_chunk_size: int = 100,
    overlap_size: int = 100,
    table_context_window: int = 3,
) -> List[Dict[str, Any]]:
    if not content_list:
        return []

    chunk_counter = 0
    all_chunks = []

    groups = _group_content_with_context(content_list, table_context_window)

    for group in groups:
        chunks = _process_content_group(
            group, document_name, output_dir, max_chunk_size, min_chunk_size, overlap_size
        )
        for c in chunks:
            c["chunk_index"] = chunk_counter
            all_chunks.append(c)
            chunk_counter += 1

    for i, chunk in enumerate(all_chunks):
        related = []
        if i > 0:
            related.append(i - 1)
        if i < len(all_chunks) - 1:
            related.append(i + 1)
        chunk["related_chunks"] = related

    logger.info(
        f"[Chunking] MineRU content_list: doc={document_name}, groups={len(groups)}, chunks={len(all_chunks)}"
    )
    return all_chunks


def _group_content_with_context(content_list: List[Dict], window: int = 3) -> List[List[Dict]]:
    if not content_list:
        return []

    claimed = [False] * len(content_list)
    groups = []

    anchor_groups = []
    for i, item in enumerate(content_list):
        if item.get("type") in ("table", "image", "equation"):
            group_indices = {i}
            for j in range(i - 1, max(i - window, -1), -1):
                if content_list[j].get("type") == "text" and not claimed[j]:
                    group_indices.add(j)
                else:
                    break
            for j in range(i + 1, min(i + window + 1, len(content_list))):
                if content_list[j].get("type") == "text" and not claimed[j]:
                    group_indices.add(j)
                else:
                    break
            anchor_groups.append(sorted(group_indices))

    if anchor_groups:
        merged = [anchor_groups[0]]
        for ag in anchor_groups[1:]:
            if ag[0] <= merged[-1][-1] + 1:
                merged[-1] = sorted(set(merged[-1]) | set(ag))
            else:
                merged.append(ag)
        anchor_groups = merged

    for ag in anchor_groups:
        group = [content_list[idx] for idx in ag]
        groups.append(group)
        for idx in ag:
            claimed[idx] = True

    remaining = [(i, item) for i, item in enumerate(content_list) if not claimed[i]]
    if remaining:
        current_group = [remaining[0][1]]
        for k in range(1, len(remaining)):
            prev_idx = remaining[k - 1][0]
            curr_idx = remaining[k][0]
            curr_item = remaining[k][1]
            if curr_idx == prev_idx + 1 and curr_item.get("type") == "text" and len(current_group) < 10:
                current_group.append(curr_item)
            else:
                groups.append(current_group)
                current_group = [curr_item]
        if current_group:
            groups.append(current_group)

    def first_page(g):
        for item in g:
            p = item.get("page_idx")
            if p is not None:
                return p
        return 0

    groups.sort(key=first_page)
    return groups


def _process_content_group(
    group: List[Dict],
    document_name: str,
    output_dir: str,
    max_chunk_size: int,
    min_chunk_size: int,
    overlap_size: int,
) -> List[Dict[str, Any]]:
    if not group:
        return []

    for item in group:
        if item.get("type") == "discarded":
            item["type"] = "text"

    types_in_group = set(item.get("type") for item in group)
    has_text = "text" in types_in_group
    has_table = "table" in types_in_group
    has_image = "image" in types_in_group
    has_equation = "equation" in types_in_group
    has_anchor = has_table or has_image or has_equation

    if has_text and has_anchor:
        return _chunk_mixed_group(group, document_name, output_dir, max_chunk_size, min_chunk_size)
    if types_in_group == {"text"}:
        return _chunk_text_group(group, document_name, max_chunk_size, min_chunk_size, overlap_size)
    if types_in_group == {"image"}:
        return _chunk_image_group(group, document_name, output_dir)
    if types_in_group == {"table"}:
        return _chunk_table_group(group, document_name, output_dir)
    if has_anchor:
        return _chunk_mixed_group(group, document_name, output_dir, max_chunk_size, min_chunk_size)

    return []


def _chunk_text_group(
    text_group: List[Dict], document_name: str,
    max_chunk_size: int, min_chunk_size: int, overlap_size: int,
) -> List[Dict[str, Any]]:
    chunks = []
    paragraphs = []
    for item in text_group:
        text = item.get("text", "").strip()
        if text:
            paragraphs.append(text)

    if not paragraphs:
        return []

    full_text = "\n\n".join(paragraphs)
    para_list = re.split(r"\n\s*\n", full_text)

    current = ""
    for para in para_list:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 > max_chunk_size and len(current) > min_chunk_size:
            if current.strip():
                page_idx = _get_page_idx(text_group)
                chunks.append({
                    "chunk_type": "text",
                    "content": current.strip(),
                    "page_idx": page_idx,
                    "metadata": {"chunk_strategy": "semantic"},
                })
            current = para
        else:
            current = (current + "\n\n" + para).strip() if current else para

    if current.strip():
        page_idx = _get_page_idx(text_group)
        chunks.append({
            "chunk_type": "text",
            "content": current.strip(),
            "page_idx": page_idx,
            "metadata": {"chunk_strategy": "semantic"},
        })

    return chunks


def _chunk_image_group(
    image_group: List[Dict], document_name: str, output_dir: str,
) -> List[Dict[str, Any]]:
    chunks = []
    for item in image_group:
        img_path = item.get("img_path")
        if not img_path:
            continue

        caption_raw = item.get("image_caption", "")
        if isinstance(caption_raw, list):
            caption = "; ".join(caption_raw) if caption_raw else ""
        else:
            caption = caption_raw or ""

        content_parts = []
        if caption:
            content_parts.append(f"[图片标题: {caption}]")
        ocr_text = item.get("ocr_text", "") or item.get("text", "")
        if ocr_text:
            content_parts.append(f"[图片内容: {ocr_text}]")

        full_img_path = os.path.join(output_dir, img_path) if not os.path.isabs(img_path) else img_path

        chunks.append({
            "chunk_type": "image",
            "content": "\n".join(content_parts) if content_parts else f"[图片: {img_path}]",
            "page_idx": item.get("page_idx"),
            "content_path": full_img_path,
            "image_path": img_path,
            "metadata": {
                "embedding_type": "visual",
                "image_caption": caption,
                "has_caption": bool(caption),
                "chunk_strategy": "image_visual",
            },
        })

        if caption:
            chunks.append({
                "chunk_type": "image",
                "content": caption,
                "page_idx": item.get("page_idx"),
                "content_path": full_img_path,
                "image_path": img_path,
                "metadata": {
                    "embedding_type": "text",
                    "image_caption": caption,
                    "has_caption": True,
                    "chunk_strategy": "image_caption",
                },
            })

    return chunks


def _chunk_table_group(
    table_group: List[Dict], document_name: str, output_dir: str,
) -> List[Dict[str, Any]]:
    chunks = []
    for item in table_group:
        table_body = item.get("table_body", "")
        if not table_body:
            continue

        caption = item.get("table_caption", [])
        footnote = item.get("table_footnote", [])
        img_path = item.get("img_path")
        table_plain_text = _html_table_to_text(table_body)

        content_parts = []
        if caption:
            cap_str = "; ".join(caption) if isinstance(caption, list) else caption
            content_parts.append(f"[表格标题: {cap_str}]")
        content_parts.append(f"[表格内容: {table_plain_text}]")
        if footnote:
            fn_str = "; ".join(footnote) if isinstance(footnote, list) else footnote
            content_parts.append(f"[表格脚注: {fn_str}]")

        content = "\n".join(content_parts)
        full_img_path = None
        if img_path:
            full_img_path = os.path.join(output_dir, img_path) if not os.path.isabs(img_path) else img_path

        if img_path:
            chunks.append({
                "chunk_type": "table",
                "content": content,
                "page_idx": item.get("page_idx"),
                "content_path": full_img_path,
                "image_path": img_path,
                "metadata": {
                    "embedding_type": "visual",
                    "table_caption": "; ".join(caption) if caption else "",
                    "table_plain_text": table_plain_text,
                    "chunk_strategy": "table_visual",
                },
            })

        chunks.append({
            "chunk_type": "table",
            "content": content,
            "page_idx": item.get("page_idx"),
            "content_path": full_img_path,
            "image_path": img_path,
            "metadata": {
                "embedding_type": "text",
                "table_caption": "; ".join(caption) if caption else "",
                "table_plain_text": table_plain_text,
                "chunk_strategy": "table_text",
            },
        })

    return chunks


def _chunk_mixed_group(
    mixed_group: List[Dict], document_name: str, output_dir: str,
    max_chunk_size: int, min_chunk_size: int,
) -> List[Dict[str, Any]]:
    chunks = []

    content_parts = []
    image_paths_in_group = []
    table_image_paths = []

    for idx, item in enumerate(mixed_group):
        item_type = item.get("type")

        if item_type == "text":
            text = item.get("text", "").strip()
            if text:
                text_level = item.get("text_level", 0)
                if text_level > 0:
                    content_parts.append(f"\n{'#' * min(text_level, 4)} {text}")
                else:
                    content_parts.append(text)

        elif item_type == "table":
            table_body = item.get("table_body", "")
            caption = item.get("table_caption", [])
            footnote = item.get("table_footnote", [])
            img_path = item.get("img_path")

            section = []
            if caption:
                cap_str = "; ".join(caption) if isinstance(caption, list) else caption
                section.append(f"[表格标题: {cap_str}]")
            if table_body:
                section.append(f"[表格内容: {_html_table_to_text(table_body)}]")
            if footnote:
                fn_str = "; ".join(footnote) if isinstance(footnote, list) else footnote
                section.append(f"[表格脚注: {fn_str}]")
            content_parts.append("\n".join(section))

            if img_path:
                full_path = os.path.join(output_dir, img_path) if not os.path.isabs(img_path) else img_path
                table_image_paths.append((img_path, full_path))

        elif item_type == "image":
            img_path = item.get("img_path", "")
            caption_raw = item.get("image_caption", "")
            if isinstance(caption_raw, list):
                caption = "; ".join(caption_raw) if caption_raw else ""
            else:
                caption = caption_raw or ""

            section = []
            if caption:
                section.append(f"[图片标题: {caption}]")
            ocr_text = item.get("ocr_text", "") or item.get("text", "")
            if ocr_text:
                section.append(f"[图片内容: {ocr_text}]")
            if section:
                content_parts.append("\n".join(section))

            if img_path:
                full_path = os.path.join(output_dir, img_path) if not os.path.isabs(img_path) else img_path
                image_paths_in_group.append((img_path, full_path))

        elif item_type == "equation":
            latex = item.get("text", "")
            if latex:
                content_parts.append(f"[公式: {latex}]")

    full_content = "\n\n".join(content_parts)
    if not full_content.strip():
        return []

    page_idx = _get_page_idx(mixed_group)

    all_visual = []
    for img_path, full_path in table_image_paths:
        all_visual.append(("table", img_path, full_path))
    for img_path, full_path in image_paths_in_group:
        all_visual.append(("image", img_path, full_path))

    chunks.append({
        "chunk_type": "mixed",
        "content": full_content,
        "page_idx": page_idx,
        "content_path": all_visual[0][2] if all_visual else None,
        "metadata": {
            "embedding_type": "text",
            "has_table": bool(table_image_paths),
            "has_image": bool(image_paths_in_group),
            "chunk_strategy": "mixed_text",
        },
    })

    for source_type, img_path, full_path in all_visual:
        chunks.append({
            "chunk_type": "mixed",
            "content": full_content,
            "page_idx": page_idx,
            "content_path": full_path,
            "image_path": img_path,
            "metadata": {
                "embedding_type": "visual",
                "source_element_type": source_type,
                "chunk_strategy": "mixed_visual",
            },
        })

    return chunks


def _html_table_to_text(html_content: str) -> str:
    if not html_content:
        return ""
    text = html_content
    text = re.sub(r"<tr[^>]*>", "\n", text)
    text = re.sub(r"<t[hd][^>]*>", " | ", text)
    text = re.sub(r"<br\s*/?>", ", ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*\|\s*", " | ", text)
    return text.strip()


def _get_page_idx(group: List[Dict]) -> Optional[int]:
    for item in group:
        p = item.get("page_idx")
        if p is not None:
            return p
    return None


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
