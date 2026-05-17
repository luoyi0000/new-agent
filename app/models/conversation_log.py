"""会话历史日志模型 — L3 冷检索"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime, timezone
from app.core.database import Base


class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_id = Column(String(36), nullable=True)
    user_message = Column(Text, nullable=False)
    agent_reply = Column(Text, nullable=False)
    intent = Column(String(20), default="other")
    tool_calls = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
