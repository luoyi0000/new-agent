"""L2 语义记忆 — ChromaDB 跨会话向量召回

复用项目的 ChromaClient 和 EmbeddingService，
每个用户独立的 ChromaDB collection 存储记忆片段。
记忆类型标签：preference / fact / interaction
"""

from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from app.core.chromadb_client import chroma_client
from app.retrieval.embedding import EmbeddingService


class SemanticMemory:
    """L2 语义记忆管理器"""

    def __init__(self):
        self.embedder = EmbeddingService()
        self.chroma = chroma_client

    def _collection_name(self, user_id: int) -> str:
        return f"memory_user_{user_id}"

    async def remember(
        self,
        user_id: int,
        text: str,
        memory_type: str = "interaction",
    ) -> str:
        """存储一段记忆到语义记忆"""
        if not user_id or not text:
            return ""

        emb = await self.embedder.embed_query(text)
        collection = self.chroma.get_or_create_collection(
            self._collection_name(user_id)
        )

        mem_id = str(uuid4())
        collection.add(
            ids=[mem_id],
            embeddings=[emb],
            documents=[text],
            metadatas=[{
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
            }],
        )
        return mem_id

    async def recall(
        self,
        user_id: int,
        query: str,
        top_k: int = 3,
        memory_type: Optional[str] = None,
    ) -> List[dict]:
        """语义召回相关记忆"""
        if not user_id or not query:
            return []

        query_vec = await self.embedder.embed_query(query)
        collection = self.chroma.get_or_create_collection(
            self._collection_name(user_id)
        )

        where = None
        if memory_type:
            where = {"type": memory_type}

        results = collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        memories = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                memories.append({
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "type": results["metadatas"][0][i].get("type", "unknown"),
                    "score": 1.0 - (results["distances"][0][i] if results["distances"] else 0),
                    "timestamp": results["metadatas"][0][i].get("timestamp", ""),
                })
        return memories

    async def forget(self, user_id: int, memory_id: str) -> bool:
        """删除指定记忆"""
        try:
            collection = self.chroma.get_or_create_collection(
                self._collection_name(user_id)
            )
            collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False

    def count(self, user_id: int) -> int:
        """查询该用户的记忆数量"""
        try:
            collection = self.chroma.get_or_create_collection(
                self._collection_name(user_id)
            )
            return collection.count()
        except Exception:
            return 0
