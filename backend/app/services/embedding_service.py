import hashlib
import math
import json
import time
from typing import List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self._model = None
        self._use_sentence_transformers = False
        logger.info(f"EmbeddingService initialized: dimension={dimension}")

    def _try_load_local_model(self, model_name: str) -> bool:
        logger.info(f"[Embedding] Attempting to load local model: {model_name}")
        start_time = time.time()
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
            self._use_sentence_transformers = True
            self.dimension = self._model.get_sentence_embedding_dimension()
            elapsed = time.time() - start_time
            logger.info(
                f"[Embedding] Local model loaded: model={model_name}, dim={self.dimension}, elapsed={elapsed:.2f}s"
            )
            return True
        except ImportError:
            logger.info(
                f"[Embedding] sentence-transformers not installed, using hash-based embedding"
            )
            return False
        except Exception as e:
            logger.warning(
                f"[Embedding] Failed to load model {model_name}: {type(e).__name__}: {e}"
            )
            return False

    def embed_texts(
        self, texts: List[str], model_name: Optional[str] = None
    ) -> List[List[float]]:
        start_time = time.time()
        logger.info(
            f"[Embedding] embed_texts called: texts_count={len(texts)}, model_name={model_name}"
        )

        if model_name and model_name != "local" and not self._use_sentence_transformers:
            self._try_load_local_model(model_name)

        if self._use_sentence_transformers and self._model:
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            result = [emb.tolist() for emb in embeddings]
            elapsed = time.time() - start_time
            logger.info(
                f"[Embedding] Embeddings generated (sentence-transformers): count={len(texts)}, dim={self.dimension}, elapsed={elapsed:.2f}s"
            )
            return result

        result = [self._hash_embed(t) for t in texts]
        elapsed = time.time() - start_time
        logger.info(
            f"[Embedding] Embeddings generated (hash-based): count={len(texts)}, dim={self.dimension}, elapsed={elapsed:.2f}s"
        )
        return result

    def embed_query(
        self, query: str, model_name: Optional[str] = None
    ) -> List[float]:
        results = self.embed_texts([query], model_name)
        return results[0]

    def _hash_embed(self, text: str) -> List[float]:
        pieces = []
        chunk_size = max(1, len(text) // self.dimension + 1)
        for i in range(self.dimension):
            piece = text[i * chunk_size : (i + 1) * chunk_size] or str(i)
            h = hashlib.md5(f"{piece}_{i}".encode()).hexdigest()
            val = int(h[:8], 16) / 0xFFFFFFFF
            pieces.append(val * 2 - 1)

        norm = math.sqrt(sum(v * v for v in pieces))
        if norm > 0:
            pieces = [v / norm for v in pieces]
        return pieces

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    @staticmethod
    def serialize_embedding(vec: List[float]) -> str:
        return json.dumps(vec)

    @staticmethod
    def deserialize_embedding(data: str) -> List[float]:
        return json.loads(data)
