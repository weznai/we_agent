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
        self._model_name: Optional[str] = None
        self._use_sentence_transformers = False
        self._api_client = None
        self._api_model: Optional[str] = None
        self._api_dimension: Optional[int] = None
        logger.info(f"EmbeddingService initialized: dimension={dimension}")

    def load_local_model(self, model_name_or_path: str) -> bool:
        logger.info(f"[Embedding] Loading local model: {model_name_or_path}")
        start_time = time.time()
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name_or_path)
            self._use_sentence_transformers = True
            self._model_name = model_name_or_path
            self._api_client = None
            self._api_model = None
            self._api_dimension = None
            self.dimension = self._model.get_embedding_dimension()
            elapsed = time.time() - start_time
            logger.info(
                f"[Embedding] Local model loaded: model={model_name_or_path}, "
                f"dim={self.dimension}, elapsed={elapsed:.2f}s"
            )
            return True
        except ImportError:
            logger.warning("[Embedding] sentence-transformers not installed, falling back to hash")
            return False
        except Exception as e:
            logger.warning(f"[Embedding] Failed to load local model {model_name_or_path}: {e}")
            return False

    def configure_api(self, api_base: str, api_key: str, model: str, dimension: int = 0):
        logger.info(f"[Embedding] Configuring API embedding: api_base={api_base}, model={model}, dim={dimension}")
        self._api_client = None
        self._api_model = model
        self._api_dimension = dimension or self.dimension
        self._use_sentence_transformers = False
        self._model = None
        self._model_name = None
        self._api_base = api_base
        self._api_key = api_key
        if dimension:
            self.dimension = dimension

    def _get_api_client(self):
        if self._api_client is None and self._api_model:
            from openai import OpenAI

            self._api_client = OpenAI(base_url=self._api_base, api_key=self._api_key)
        return self._api_client

    def _try_load_local_model(self, model_name: str) -> bool:
        if self._model_name == model_name and self._use_sentence_transformers:
            return True
        return self.load_local_model(model_name)

    def embed_texts(
        self, texts: List[str], model_name: Optional[str] = None
    ) -> List[List[float]]:
        start_time = time.time()
        logger.info(
            f"[Embedding] embed_texts: count={len(texts)}, model_name={model_name}"
        )

        if model_name and model_name != "local":
            if not self._use_sentence_transformers or self._model_name != model_name:
                self._try_load_local_model(model_name)

        if self._api_model:
            return self._embed_via_api(texts)

        if self._use_sentence_transformers and self._model:
            return self._embed_local_batch(texts)

        result = [self._hash_embed(t) for t in texts]
        elapsed = time.time() - start_time
        logger.info(
            f"[Embedding] Generated (hash): count={len(texts)}, "
            f"dim={self.dimension}, elapsed={elapsed:.2f}s"
        )
        return result

    def _embed_local_batch(self, texts: List[str], batch_size: int = 8) -> List[List[float]]:
        start_time = time.time()
        all_results = []
        total = len(texts)
        for i in range(0, total, batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self._model.encode(batch, normalize_embeddings=True)
            all_results.extend([emb.tolist() for emb in embeddings])
            logger.info(
                f"[Embedding] Batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size}: "
                f"encoded {len(batch)} texts"
            )
        elapsed = time.time() - start_time
        logger.info(
            f"[Embedding] Generated (local): count={total}, "
            f"dim={self.dimension}, elapsed={elapsed:.2f}s"
        )
        return all_results

    def embed_query(
        self, query: str, model_name: Optional[str] = None
    ) -> List[float]:
        results = self.embed_texts([query], model_name)
        return results[0]

    def _embed_via_api(self, texts: List[str]) -> List[List[float]]:
        start_time = time.time()
        client = self._get_api_client()
        if not client:
            return [self._hash_embed(t) for t in texts]

        try:
            response = client.embeddings.create(
                model=self._api_model,
                input=texts,
            )
            result = [item.embedding for item in response.data]
            elapsed = time.time() - start_time
            logger.info(
                f"[Embedding] Generated (API): count={len(texts)}, "
                f"model={self._api_model}, elapsed={elapsed:.2f}s"
            )
            return result
        except Exception as e:
            logger.error(f"[Embedding] API call failed: {e}, falling back to hash")
            return [self._hash_embed(t) for t in texts]

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

    @property
    def is_loaded(self) -> bool:
        return self._use_sentence_transformers or self._api_model is not None

    @property
    def model_info(self) -> str:
        if self._use_sentence_transformers:
            return f"local:{self._model_name}"
        if self._api_model:
            return f"api:{self._api_model}"
        return "hash"

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


class RerankService:
    def __init__(self):
        self._model = None
        self._model_name: Optional[str] = None
        self._api_client = None
        self._api_model: Optional[str] = None
        self._api_base: Optional[str] = None
        self._api_key: Optional[str] = None

    def load_local_model(self, model_name_or_path: str) -> bool:
        logger.info(f"[Rerank] Loading local model: {model_name_or_path}")
        start_time = time.time()
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(model_name_or_path)
            self._model_name = model_name_or_path
            self._api_client = None
            self._api_model = None
            elapsed = time.time() - start_time
            logger.info(
                f"[Rerank] Local model loaded: model={model_name_or_path}, elapsed={elapsed:.2f}s"
            )
            return True
        except ImportError:
            logger.warning("[Rerank] sentence-transformers not installed")
            return False
        except Exception as e:
            logger.warning(f"[Rerank] Failed to load local model {model_name_or_path}: {e}")
            return False

    def configure_api(self, api_base: str, api_key: str, model: str):
        logger.info(f"[Rerank] Configuring API: api_base={api_base}, model={model}")
        self._api_client = None
        self._api_model = model
        self._api_base = api_base
        self._api_key = api_key
        self._model = None
        self._model_name = None

    def _get_api_client(self):
        if self._api_client is None and self._api_model:
            from openai import OpenAI

            self._api_client = OpenAI(base_url=self._api_base, api_key=self._api_key)
        return self._api_client

    def rerank(
        self, query: str, documents: List[str], top_k: int = 5
    ) -> List[dict]:
        if not documents:
            return []

        if self._model:
            return self._rerank_local(query, documents, top_k)

        if self._api_model:
            return self._rerank_api(query, documents, top_k)

        return [
            {"index": i, "text": doc, "score": 1.0 - i * 0.01}
            for i, doc in enumerate(documents[:top_k])
        ]

    def _rerank_local(
        self, query: str, documents: List[str], top_k: int
    ) -> List[dict]:
        start_time = time.time()
        pairs = [[query, doc] for doc in documents]
        scores = self._model.predict(pairs)
        ranked = sorted(
            [{"index": i, "text": documents[i], "score": float(scores[i])} for i in range(len(documents))],
            key=lambda x: x["score"],
            reverse=True,
        )
        elapsed = time.time() - start_time
        logger.info(
            f"[Rerank] Local rerank: docs={len(documents)}, top_k={top_k}, elapsed={elapsed:.2f}s"
        )
        return ranked[:top_k]

    def _rerank_api(
        self, query: str, documents: List[str], top_k: int
    ) -> List[dict]:
        start_time = time.time()
        client = self._get_api_client()
        if not client:
            return [
                {"index": i, "text": doc, "score": 1.0}
                for i, doc in enumerate(documents[:top_k])
            ]
        try:
            response = client.chat.completions.create(
                model=self._api_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a relevance scoring assistant. Given a query and a list of documents, "
                            "return a JSON array of objects with 'index' (0-based) and 'score' (0-1) fields, "
                            "sorted by relevance descending. Return only the JSON array."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nDocuments:\n"
                        + "\n".join(f"[{i}] {doc[:200]}" for i, doc in enumerate(documents))
                        + f"\n\nReturn top {top_k} results as JSON array.",
                    },
                ],
                temperature=0,
            )
            import json as _json

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            results = _json.loads(content)
            for r in results:
                idx = r.get("index", 0)
                r["text"] = documents[idx] if idx < len(documents) else ""
            elapsed = time.time() - start_time
            logger.info(f"[Rerank] API rerank: docs={len(documents)}, elapsed={elapsed:.2f}s")
            return results[:top_k]
        except Exception as e:
            logger.warning(f"[Rerank] API rerank failed: {e}")
            return [
                {"index": i, "text": doc, "score": 1.0 - i * 0.01}
                for i, doc in enumerate(documents[:top_k])
            ]

    @property
    def is_loaded(self) -> bool:
        return self._model is not None or self._api_model is not None
