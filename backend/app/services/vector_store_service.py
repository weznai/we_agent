import os
from typing import List, Optional, Dict, Any

from ..config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VectorStoreService:
    _instance = None

    @classmethod
    def get_instance(cls) -> "VectorStoreService":
        if cls._instance is None:
            settings = get_settings()
            cls._instance = cls(settings.CHROMADB_PATH, settings.CHROMADB_COLLECTION)
        return cls._instance

    def __init__(self, db_path: str, collection_name: str):
        import chromadb

        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"VectorStoreService initialized: db_path={db_path}, collection={collection_name}"
        )

    def _rebuild_collection(self, reason: str):
        logger.warning(f"[VectorStore] {reason}. Recreating collection.")
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _check_and_rebuild_dim(self, dim: int):
        try:
            count = self.collection.count()
            if count == 0:
                return
            peek = self.collection.peek(limit=1)
            embs = peek.get("embeddings")
            if embs is not None and len(embs) > 0:
                stored_dim = len(embs[0])
                if stored_dim != dim:
                    self._rebuild_collection(
                        f"Dimension mismatch: collection={stored_dim}d, new={dim}d"
                    )
        except Exception as e:
            logger.warning(f"[VectorStore] Dimension check failed: {e}")
            try:
                self._rebuild_collection(f"Dimension check error: {e}")
            except Exception as e2:
                logger.error(f"[VectorStore] Rebuild failed: {e2}")

    def add_chunks(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ):
        if not ids:
            return
        self._check_and_rebuild_dim(len(embeddings[0]))
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info(f"[VectorStore] Upserted {len(ids)} chunks")

    def search(
        self,
        query_embedding: List[float],
        user_id: int,
        group_id: Optional[int] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        self._check_and_rebuild_dim(len(query_embedding))

        if group_id is not None:
            where: Dict[str, Any] = {"$and": [
                {"user_id": user_id},
                {"group_id": group_id},
            ]}
        else:
            where = {"user_id": user_id}

        n_results = min(top_k * 3, 50)
        try:
            count = self.collection.count()
            if count == 0:
                return []
            n_results = min(n_results, count)
        except Exception:
            pass

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            if "dimension" in str(e).lower():
                self._rebuild_collection(f"Query dimension error: {e}")
                return []
            raise

        items = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                similarity = 1.0 - distance
                items.append(
                    {
                        "id": doc_id,
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": similarity,
                    }
                )

        items.sort(key=lambda x: x["score"], reverse=True)
        return items[:top_k]

    def delete_by_knowledge_id(self, knowledge_id: int):
        try:
            self.collection.delete(where={"knowledge_id": knowledge_id})
            logger.info(
                f"[VectorStore] Deleted chunks for knowledge_id={knowledge_id}"
            )
        except Exception as e:
            logger.warning(f"[VectorStore] Delete failed: {e}")

    def get_chunks_by_knowledge_id(self, knowledge_id: int) -> List[Dict[str, Any]]:
        try:
            results = self.collection.get(
                where={"knowledge_id": knowledge_id},
                include=["documents", "metadatas"],
            )
            chunks = []
            if results and results["ids"]:
                for i, doc_id in enumerate(results["ids"]):
                    meta = results["metadatas"][i]
                    chunks.append(
                        {
                            "id": doc_id,
                            "content": results["documents"][i],
                            "chunk_index": meta.get("chunk_index", 0),
                            "char_count": len(results["documents"][i]),
                        }
                    )
            chunks.sort(key=lambda x: x["chunk_index"])
            return chunks
        except Exception as e:
            logger.warning(f"[VectorStore] Get chunks failed: {e}")
            return []
