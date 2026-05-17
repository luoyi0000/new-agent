"""三层记忆 API — 为前端展示和管理记忆状态"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.memory import MemoryManager

router = APIRouter(prefix="/memory", tags=["记忆管理"])


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class WorkingMemoryResponse(BaseModel):
    """L1 工作记忆"""
    preferences: dict
    recent_intents: list[str]
    key_facts: list[str]
    session_count: int
    summary_text: str


class SemanticMemoryItem(BaseModel):
    """L2 语义记忆条目"""
    id: str
    text: str
    memory_type: str
    score: float
    timestamp: str


class HistoryItem(BaseModel):
    """L3 历史会话条目"""
    id: int
    user_message: str
    agent_reply: str
    intent: str
    created_at: str


class MemoryStatusResponse(BaseModel):
    """三层记忆概览"""
    has_working_memory: bool
    semantic_count: int
    history_count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
def memory_status(
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """三层记忆概览（各层状态和数量）"""
    user_id = int(payload["sub"])
    mm = MemoryManager(db)

    l1 = mm.working.load(user_id)
    l2_count = mm.semantic.count(user_id)
    l3_count = mm.history.count_by_user(user_id)

    return MemoryStatusResponse(
        has_working_memory=bool(l1),
        semantic_count=l2_count,
        history_count=l3_count,
    )


@router.get("/working")
def get_working_memory(
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取 L1 工作记忆（用户画像）"""
    user_id = int(payload["sub"])
    mm = MemoryManager(db)

    import json
    from app.memory.working_memory import UserMemoryModel

    record = db.query(UserMemoryModel).filter(
        UserMemoryModel.user_id == user_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="暂无工作记忆")

    return WorkingMemoryResponse(
        preferences=json.loads(record.preferences or "{}"),
        recent_intents=json.loads(record.recent_intents or "[]"),
        key_facts=json.loads(record.key_facts or "[]"),
        session_count=record.session_count or 0,
        summary_text=mm.working.load(user_id),
    )


@router.get("/semantic")
async def get_semantic_memories(
    query: str = Query("", description="搜索关键词，为空则返回所有"),
    memory_type: Optional[str] = Query(None, description="按类型过滤：preference/fact/interaction"),
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取 L2 语义记忆"""
    user_id = int(payload["sub"])
    mm = MemoryManager(db)

    if query:
        results = await mm.semantic.recall(
            user_id, query, top_k=20, memory_type=memory_type
        )
    else:
        results = await mm.semantic.recall(
            user_id, "", top_k=20, memory_type=memory_type
        )

    return {
        "total": len(results),
        "memories": [
            SemanticMemoryItem(
                id=r["id"],
                text=r["text"],
                memory_type=r["type"],
                score=r["score"],
                timestamp=r.get("timestamp", ""),
            )
            for r in results
        ],
    }


@router.get("/history")
def get_history(
    keyword: str = Query("", description="搜索关键词"),
    limit: int = Query(10, description="返回条数", ge=1, le=50),
    intent_filter: Optional[str] = Query(None, description="按意图过滤"),
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取 L3 历史会话记录"""
    user_id = int(payload["sub"])
    mm = MemoryManager(db)

    if keyword:
        results = mm.history.search(
            user_id, keyword, limit=limit, intent_filter=intent_filter
        )
    else:
        results = mm.history.get_recent(user_id, limit=limit)
        if intent_filter:
            results = [r for r in results if r["intent"] == intent_filter]

    return {
        "total": len(results),
        "history": [
            HistoryItem(
                id=r["id"],
                user_message=r["user_message"],
                agent_reply=r["agent_reply"],
                intent=r["intent"],
                created_at=r["created_at"],
            )
            for r in results
        ],
    }


@router.delete("/semantic/{memory_id}")
async def forget_memory(
    memory_id: str,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除指定语义记忆"""
    user_id = int(payload["sub"])
    mm = MemoryManager(db)

    ok = await mm.semantic.forget(user_id, memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="记忆不存在或删除失败")

    return {"status": "ok", "message": "记忆已删除"}


@router.delete("/working")
def clear_working_memory(
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """清除当前用户的工作记忆"""
    user_id = int(payload["sub"])
    from app.memory.working_memory import UserMemoryModel

    record = db.query(UserMemoryModel).filter(
        UserMemoryModel.user_id == user_id
    ).first()

    if record:
        db.delete(record)
        db.flush()
        return {"status": "ok", "message": "工作记忆已清除"}

    raise HTTPException(status_code=404, detail="暂无工作记忆")
