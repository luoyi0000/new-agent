"""应用配置管理

配置优先级：环境变量 > config.yaml > 默认值
"""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
import yaml

# ---------------------------------------------------------------------------
# YAML 配置加载
# ---------------------------------------------------------------------------
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def load_yaml_config() -> dict:
    """加载 config.yaml，文件不存在时返回空字典"""
    if not _CONFIG_PATH.exists():
        return {}
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


YAML_CONFIG = load_yaml_config()


def _yaml_val(*keys: str, default=None):
    """从 YAML_CONFIG 中安全读取嵌套值"""
    val = YAML_CONFIG
    for k in keys:
        if not isinstance(val, dict):
            return default
        val = val.get(k)
        if val is None:
            return default
    return val


# ---------------------------------------------------------------------------
# Pydantic Settings（环境变量覆盖 YAML）
# ---------------------------------------------------------------------------
class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "图书馆智能服务系统"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # PostgreSQL
    DATABASE_URL: str = "postgresql://library_user:library_pass@localhost:5432/library"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chromadb"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # LLM — 留空则 fallback 到 YAML
    MODEL_PROVIDER: str = ""
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_MODEL: str = ""

    # Embedding — 留空则 fallback 到 YAML
    EMBEDDING_PROVIDER: str = ""
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_BASE_URL: Optional[str] = None
    EMBEDDING_MODEL: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # OpenTelemetry
    OTLP_ENDPOINT: str = "http://localhost:4318"

    class Config:
        env_file = ".env"
        extra = "allow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 环境变量未设置时回退到 YAML
        if not self.MODEL_PROVIDER:
            self.MODEL_PROVIDER = _yaml_val("llm", "provider", default="deepseek")
        if not self.LLM_API_KEY:
            self.LLM_API_KEY = _yaml_val("llm", "api_key")
        if not self.LLM_BASE_URL:
            self.LLM_BASE_URL = _yaml_val("llm", "base_url")
        if not self.LLM_MODEL:
            self.LLM_MODEL = _yaml_val("llm", "model", default="deepseek-chat")
        if not self.EMBEDDING_PROVIDER:
            self.EMBEDDING_PROVIDER = _yaml_val("embedding", "provider", default="openai")
        if not self.EMBEDDING_API_KEY:
            self.EMBEDDING_API_KEY = _yaml_val("embedding", "api_key")
        if not self.EMBEDDING_BASE_URL:
            self.EMBEDDING_BASE_URL = _yaml_val("embedding", "base_url")
        if not self.EMBEDDING_MODEL:
            self.EMBEDDING_MODEL = _yaml_val("embedding", "model", default="text-embedding-v3")


settings = Settings()
