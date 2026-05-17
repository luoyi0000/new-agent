"""数据摄取管线

将数据库中的图书和政策文档分块、嵌入后写入 ChromaDB。
"""
from typing import List
from sqlalchemy.orm import Session

from app.core.chromadb_client import ChromaClient
from app.retrieval.embedding import EmbeddingService
from app.retrieval.chunker import TextChunker
from app.repositories.book_repository import BookRepository
from app.repositories.policy_repository import PolicyRepository


class IngestionPipeline:
    """索引构建管线"""

    def __init__(self, db: Session):
        self.db = db
        self.embedder = EmbeddingService()
        self.chunker = TextChunker()
        self.chroma = ChromaClient()

    async def build_book_index(self):
        """构建图书索引"""
        collection = self.chroma.get_or_create_collection("library_books")
        repo = BookRepository(self.db)
        books = repo.get_all()

        chunks = []
        for book in books:
            book_dict = {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "description": book.description,
                "location": book.location or "",
            }
            chunks.extend(self.chunker.chunk_book(book_dict))

        if not chunks:
            return {"indexed": 0}

        texts = [c["text"] for c in chunks]
        metadatas = [
            {k: str(v) for k, v in c.items() if k != "text"}
            for c in chunks
        ]
        ids = [f"book_{c['chunk_index']}_{i}" for i, c in enumerate(chunks)]

        embeddings = await self.embedder.embed_documents(texts)

        collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return {"indexed": len(chunks)}

    async def build_policy_index(self):
        """构建政策文档索引"""
        collection = self.chroma.get_or_create_collection("library_policies")
        repo = PolicyRepository(self.db)
        docs = repo.get_all()

        chunks = []
        for doc in docs:
            doc_dict = {
                "id": doc.id,
                "title": doc.title,
                "content": doc.content,
                "category": doc.category,
            }
            chunks.extend(self.chunker.chunk_policy(doc_dict))

        if not chunks:
            return {"indexed": 0}

        texts = [c["text"] for c in chunks]
        metadatas = [
            {k: str(v) for k, v in c.items() if k != "text"}
            for c in chunks
        ]
        ids = [f"policy_{c['chunk_index']}_{i}" for i, c in enumerate(chunks)]

        embeddings = await self.embedder.embed_documents(texts)

        collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return {"indexed": len(chunks)}

    async def build_all(self):
        """构建所有索引"""
        return {
            "books": await self.build_book_index(),
            "policies": await self.build_policy_index(),
        }
