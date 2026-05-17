"""文本分块策略

支持基于 Token 计数的语义分块，用于 RAG 检索。
"""
from typing import List


class TextChunker:
    """智能文本分块器"""

    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, metadata: dict = None) -> List[dict]:
        """将长文本按段落和长度切块"""
        paragraphs = text.split("\n\n")
        chunks = []
        buffer = []
        buffer_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para_len = len(para)

            if buffer_len + para_len > self.chunk_size and buffer:
                chunk_text = "\n\n".join(buffer)
                chunks.append(self._make_chunk(chunk_text, len(chunks), metadata))
                # 保留 overlap
                overlap_texts = []
                overlap_len = 0
                for b in reversed(buffer):
                    bl = len(b)
                    if overlap_len + bl > self.overlap:
                        break
                    overlap_texts.insert(0, b)
                    overlap_len += bl
                buffer = overlap_texts
                buffer_len = overlap_len

            buffer.append(para)
            buffer_len += para_len

        if buffer:
            chunk_text = "\n\n".join(buffer)
            chunks.append(self._make_chunk(chunk_text, len(chunks), metadata))

        return chunks

    def _make_chunk(self, text: str, index: int, metadata: dict = None) -> dict:
        chunk = {
            "text": text,
            "chunk_index": index,
        }
        if metadata:
            chunk.update(metadata)
        return chunk

    def chunk_book(self, book: dict) -> List[dict]:
        """将图书信息分块"""
        text_parts = [f"书名：{book.get('title', '')}"]
        if book.get("author"):
            text_parts.append(f"作者：{book['author']}")
        if book.get("description"):
            text_parts.append(f"简介：{book['description']}")
        text = "\n\n".join(text_parts)
        metadata = {
            "book_id": book.get("id"),
            "type": "book",
            "title": book.get("title", ""),
            "author": book.get("author", ""),
            "location": book.get("location", ""),
        }
        return self.chunk_text(text, metadata)

    def chunk_policy(self, doc: dict) -> List[dict]:
        """将政策文档分块"""
        text = f"标题：{doc.get('title', '')}\n\n内容：{doc.get('content', '')}"
        return self.chunk_text(text, {
            "doc_id": doc.get("id"),
            "category": doc.get("category"),
            "type": "policy",
        })
