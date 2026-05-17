"""ChromaDB 连接封装"""
import chromadb
from chromadb.config import Settings
from app.config import settings


class ChromaClient:
    """ChromaDB 客户端单例"""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    def get_or_create_collection(self, name: str):
        """获取或创建集合"""
        return self.client.get_or_create_collection(name)

    def delete_collection(self, name: str):
        """删除集合"""
        self.client.delete_collection(name)


chroma_client = ChromaClient()
