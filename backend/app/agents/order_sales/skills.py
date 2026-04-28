import json
from typing import Optional

from langchain_core.tools import tool as lc_tool

from ...database import SessionLocal
from ...utils.logger import get_logger

logger = get_logger(__name__)


def create_knowledge_search_tool(user_id: int, group_id: Optional[int] = None):
    @lc_tool
    def knowledge_search(query: str) -> str:
        """搜索知识库获取相关信息。当用户询问产品说明、业务规则、常见问题等知识库中可能包含的信息时使用此工具。
        搜索结果包含相关文档片段和来源，帮助你提供更准确的回答。

        Args:
            query: 搜索查询语句，用于在知识库中查找相关文档
        """
        logger.info(f"[Tool knowledge_search] Invoked: query={query}, user_id={user_id}, group_id={group_id}")
        tool_db = SessionLocal()
        try:
            from ...services import knowledge_service
            results = knowledge_service.search_for_agent(user_id, query, group_id, top_k=5, db=tool_db)
            if not results:
                return json.dumps({"message": "未在知识库中找到相关信息", "results": []}, ensure_ascii=False)
            for r in results:
                img_paths = r.get("image_paths") or []
                if r.get("content_path") and r["content_path"] not in img_paths:
                    img_paths.append(r["content_path"])
                r["image_files"] = [p.replace("\\", "/").split("/")[-1] for p in img_paths if p]
            return json.dumps({"results": results}, ensure_ascii=False, separators=(",", ":"))
        except Exception as e:
            logger.error(f"[Tool knowledge_search] Failed: {e}")
            return json.dumps({"error": f"知识库搜索失败: {str(e)}"}, ensure_ascii=False)
        finally:
            tool_db.close()

    return knowledge_search
