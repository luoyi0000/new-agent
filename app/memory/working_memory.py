"""L1 工作记忆 — 用户画像与偏好

每个用户维护一个结构化工作记忆，存储在 user_memories 表中。
会话开始时加载为自然语言片段注入 System Prompt，
会话结束后根据新交互更新。
"""

import json
import re
from datetime import datetime, timezone
from collections import Counter
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import Session
from app.core.database import Base


class UserMemoryModel(Base):
    """工作记忆持久化模型"""
    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    preferences = Column(Text, default="{}")      # JSON: 偏好楼层/区域/时段
    recent_intents = Column(Text, default="[]")    # JSON: 最近 5 次意图
    key_facts = Column(Text, default="[]")         # JSON: 关键事实（max 5）
    session_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WorkingMemory:
    """L1 工作记忆管理器"""

    MAX_FACTS = 5
    MAX_INTENTS = 5

    # 识别用户偏好输入的正则模式
    PREFERENCE_PATTERNS = [
        (r"(?:喜欢|爱|常去)\s*(?:坐\s*)?([\dA-F]+F)", "preferred_floor"),
        (r"(?:喜欢|爱|常坐|常去|去)\s*(静音|讨论|安静|沉浸)区", "preferred_zone"),
        (r"(?:喜欢|爱|常在?)\s*(\d+:\d+)", "preferred_time"),
    ]

    # 识别用户关键事实的正则模式
    FACT_PATTERNS = [
        r"我(?:是|学)\s*(.{1,20})",
        r"我(?:叫|姓)\s*(.{1,10})",
        r"我(?:研究|学习|搞)\s*(.{1,20})",
    ]

    def __init__(self, db: Session):
        self.db = db

    def load(self, user_id: int) -> str:
        """加载用户工作记忆 → 格式化为自然语言片段"""
        if not user_id:
            return ""

        record = self.db.query(UserMemoryModel).filter(
            UserMemoryModel.user_id == user_id
        ).first()
        if not record:
            return ""

        parts = []
        preferences = json.loads(record.preferences or "{}")
        intents = json.loads(record.recent_intents or "[]")
        facts = json.loads(record.key_facts or "[]")

        if preferences:
            lines = []
            if preferences.get("preferred_floor"):
                lines.append(f"常去楼层：{preferences['preferred_floor']}")
            if preferences.get("preferred_zone"):
                lines.append(f"偏好区域：{preferences['preferred_zone']}")
            if preferences.get("preferred_time"):
                lines.append(f"常用时段：{preferences['preferred_time']}")
            if lines:
                parts.append("用户偏好：" + "；".join(lines))

        if facts:
            parts.append("重要信息：" + "；".join(facts[-3:]))

        if intents:
            counter = Counter(intents)
            top_intent = counter.most_common(1)[0][0]
            parts.append(f"近期常做：{top_intent}")

        if record.session_count > 1:
            parts.append(f"来访次数：{record.session_count} 次")

        return "；".join(parts) if parts else ""

    def update(self, user_id: int, intent: str, query: str):
        """根据本轮交互更新工作记忆"""
        if not user_id:
            return

        record = self.db.query(UserMemoryModel).filter(
            UserMemoryModel.user_id == user_id
        ).first()

        if not record:
            record = UserMemoryModel(user_id=user_id)
            self.db.add(record)

        # 更新会话次数
        record.session_count = (record.session_count or 0) + 1

        # 更新最近意图
        intents = json.loads(record.recent_intents or "[]")
        intents.append(intent)
        if len(intents) > self.MAX_INTENTS:
            intents = intents[-self.MAX_INTENTS:]
        record.recent_intents = json.dumps(intents)

        # 自动提取偏好
        preferences = json.loads(record.preferences or "{}")
        self._extract_preferences(query, preferences)
        record.preferences = json.dumps(preferences)

        # 关键事实提取
        facts = json.loads(record.key_facts or "[]")
        new_facts = self._extract_facts(query)
        for f in new_facts:
            if f not in facts:
                facts.append(f)
                if len(facts) > self.MAX_FACTS:
                    facts.pop(0)
        record.key_facts = json.dumps(facts)

        record.last_updated = datetime.now(timezone.utc)
        self.db.flush()

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _extract_preferences(self, text: str, prefs: dict):
        """从用户输入中提取偏好信息"""
        for pattern, key in self.PREFERENCE_PATTERNS:
            m = re.search(pattern, text)
            if m:
                prefs[key] = m.group(1).strip()

    def _extract_facts(self, text: str) -> list:
        """从用户输入中提取声明性事实"""
        facts = []
        for pattern in self.FACT_PATTERNS:
            m = re.search(pattern, text)
            if m:
                facts.append(m.group(0).strip())
        return facts
