"""L3 冷检索 — PostgreSQL 全文搜索历史会话

基于 ConversationLog 模型，通过 SQL ILIKE 实现
历史会话的精确检索。
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.conversation_log import ConversationLog


class HistoryMemory:
    """L3 冷检索管理器"""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        user_id: int,
        user_message: str,
        agent_reply: str,
        intent: str = "other",
        session_id: Optional[str] = None,
        tool_calls: Optional[list] = None,
    ) -> int:
        """记录一条会话历史"""
        if not user_id:
            return 0

        log_entry = ConversationLog(
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            agent_reply=agent_reply,
            intent=intent,
            tool_calls=tool_calls,
        )
        self.db.add(log_entry)
        self.db.flush()
        return log_entry.id

    def search(
        self,
        user_id: int,
        keyword: str,
        limit: int = 5,
        intent_filter: Optional[str] = None,
    ) -> List[dict]:
        """全文检索历史会话"""
        if not user_id:
            return []

        query = self.db.query(ConversationLog).filter(
            ConversationLog.user_id == user_id
        )

        if keyword:
            like_pattern = f"%{keyword}%"
            query = query.filter(
                ConversationLog.user_message.ilike(like_pattern)
                | ConversationLog.agent_reply.ilike(like_pattern)
            )

        if intent_filter:
            query = query.filter(ConversationLog.intent == intent_filter)

        results = (
            query.order_by(desc(ConversationLog.created_at))
            .limit(limit)
            .all()
        )

        return [
            {
                "id": r.id,
                "user_message": r.user_message[:200],
                "agent_reply": r.agent_reply[:200],
                "intent": r.intent,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in results
        ]

    def get_recent(
        self,
        user_id: int,
        limit: int = 10,
    ) -> List[dict]:
        """获取用户最近的会话记录"""
        return self.search(user_id, keyword="", limit=limit)

    def count_by_user(self, user_id: int) -> int:
        """统计该用户的会话总数"""
        return (
            self.db.query(ConversationLog)
            .filter(ConversationLog.user_id == user_id)
            .count()
        )
