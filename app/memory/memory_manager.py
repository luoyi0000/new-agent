"""MemoryManager — 三层记忆统一编排器

编排 L1 工作记忆、L2 语义记忆、L3 冷检索的读写流程：
1. load_context(): 会话开始时，加载三层记忆并组合为上下文字符串
2. update(): 会话结束后，更新三层记忆
"""

from typing import Optional
from sqlalchemy.orm import Session

from .working_memory import WorkingMemory
from .semantic_memory import SemanticMemory
from .history_memory import HistoryMemory


class MemoryManager:
    """三层记忆编排器"""

    # 高价值意图列表（这些意图值得存入 L2 语义记忆）
    IMPORTANT_INTENTS = {"book_seat", "search_book", "policy_query", "cancel_appointment"}

    def __init__(self, db: Session):
        self.db = db
        self.working = WorkingMemory(db)
        self.semantic = SemanticMemory()
        self.history = HistoryMemory(db)

    async def load_context(self, user_id: int, user_query: str) -> str:
        """加载三层记忆 → 组合为上下文片段"""
        if not user_id:
            return ""

        parts = []

        # L1: 工作记忆（用户画像摘要）
        l1 = self.working.load(user_id)
        if l1:
            parts.append(f"[用户画像] {l1}")

        # L2: 语义记忆（根据当前查询召回相关记忆）
        l2_results = await self.semantic.recall(user_id, user_query, top_k=3)
        if l2_results:
            mem_lines = []
            for m in l2_results:
                if m["score"] > 0.5:
                    mem_lines.append(m["text"][:150])
            if mem_lines:
                parts.append("[历史相关]" + "；".join(mem_lines))

        # L3: 冷检索（精确匹配历史关键词）
        l3_results = self.history.search(user_id, user_query, limit=2)
        if l3_results:
            found = []
            for r in l3_results:
                found.append(f"({r['created_at'][:10]}) {r['user_message'][:60]}")
            if found:
                parts.append("[历史对话]" + "；".join(found))

        return "\n".join(parts) if parts else ""

    async def update(
        self,
        user_id: int,
        user_query: str,
        agent_reply: str,
        intent: str = "other",
        session_id: Optional[str] = None,
        tool_calls: Optional[list] = None,
    ):
        """会话结束后更新三层记忆"""
        if not user_id:
            return

        # L3: 记录完整会话（始终记录）
        self.history.log(
            user_id=user_id,
            user_message=user_query,
            agent_reply=agent_reply,
            intent=intent,
            session_id=session_id,
            tool_calls=tool_calls,
        )

        # L1: 更新工作记忆
        self.working.update(user_id, intent, user_query)

        # L2: 高价值意图存入语义记忆
        if intent in self.IMPORTANT_INTENTS:
            memory_text = f"用户查询{intent}: {user_query}"
            await self.semantic.remember(
                user_id=user_id,
                text=memory_text,
                memory_type="interaction",
            )
