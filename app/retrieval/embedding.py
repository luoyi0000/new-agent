"""嵌入模型服务封装

支持本地 sentence-transformers 和远程 API 两种模式。
默认使用本地模型，无需额外配置。
"""
from typing import List, Optional
from app.config import settings


class EmbeddingService:
    """统一嵌入服务

    当配置了 LLM_API_KEY 时使用远程 API，否则回退到本地模型。
    """

    def __init__(self):
        self._model = None
        self._use_local = not bool(settings.EMBEDDING_API_KEY)

    def _init_local_model(self):
        """延迟初始化本地嵌入模型"""
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self._dimension = self._model.get_sentence_embedding_dimension()

    async def embed_query(self, text: str) -> List[float]:
        """嵌入查询文本"""
        if self._use_local:
            self._init_local_model()
            vec = self._model.encode(text, normalize_embeddings=True)
            return vec.tolist()
        return (await self._remote_embed([text]))[0]

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文档"""
        if self._use_local:
            self._init_local_model()
            vecs = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return vecs.tolist()
        return await self._remote_embed(texts)

    async def _remote_embed(self, texts: List[str]) -> List[List[float]]:
        """使用远程 API 嵌入（自动分批，每批不超过 10 条）"""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
        )
        BATCH_SIZE = 10
        all_embeddings = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            resp = await client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=batch,
            )
            all_embeddings.extend(item.embedding for item in resp.data)
        return all_embeddings

    @property
    def dimension(self) -> int:
        """返回向量维度"""
        if self._use_local:
            self._init_local_model()
            return self._dimension
        return 1024  # qwen text-embedding-v2 维度
