"""混合检索引擎 — 仅使用多语言向量检索

改造说明：
- BM25 用 str.split() 无法正确分词中文，已移除
- Cross-Encoder ms-marco-MiniLM-L-6-v2 为纯英文模型，会破坏中文相关性评分，已移除
- 仅保留 paraphrase-multilingual-MiniLM-L12-v2 多语言向量检索
"""
from typing import List, Dict, Optional

from app.core.chromadb_client import ChromaClient
from app.retrieval.embedding import EmbeddingService


class HybridSearch:
    """混合检索（简化版：仅向量检索）"""

    def __init__(self):
        self.embedder = EmbeddingService()
        self.chroma = ChromaClient()

    async def search(
        self,
        query: str,
        collection_name: str = "library_books",
        top_k: int = 10,
        rerank: bool = False,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """检索主入口 — 仅使用多语言向量检索"""
        return await self._dense_search(query, collection_name, top_k, metadata_filter)

    async def _dense_search(
        self, query: str, collection_name: str, top_k: int,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """向量相似度召回"""
        query_vec = await self.embedder.embed_query(query)
        collection = self.chroma.get_or_create_collection(collection_name)

        where = None
        if metadata_filter:
            where = {k: v for k, v in metadata_filter.items()}

        results = collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        dense_list = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                dense_list.append({
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "score": 1.0 - (results["distances"][0][i] if results["distances"] else 0),
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                })
        return dense_list
