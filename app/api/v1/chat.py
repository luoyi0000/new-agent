"""AI 智能问答 API（SSE 流式）"""
import re
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.agents.orchestrator import AgentOrchestrator

# 兜底清理回复中的 DSML/XML 标记
_TOOL_TAG_PATTERNS = [
    (r'<\|\|DSML\|\|invoke[^>]*>.*?</\|\|DSML\|\|invoke>', re.DOTALL),
    (r'<\|\|DSML\|\|parameter[^>]*>.*?</\|\|DSML\|\|parameter>', re.DOTALL),
    (r'<\|\|DSML\|\|tool_calls>\s*', 0),
    (r'\s*</\|\|DSML\|\|tool_calls>', 0),
    (r'<invoke[^>]*>.*?</invoke>', re.DOTALL),
    (r'<parameter[^>]*>.*?</parameter>', re.DOTALL),
    (r'<tool_calls>\s*', 0),
    (r'\s*</tool_calls>', 0),
]


def _strip_tool_tags(text: str) -> str:
    for pat, flags in _TOOL_TAG_PATTERNS:
        text = re.sub(pat, '', text, flags=flags)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


router = APIRouter(prefix="/chat", tags=["智能问答"])


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.post("/")
async def chat(
    req: ChatRequest,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """普通问答接口（非流式）"""
    user_id = int(payload["sub"])
    orchestrator = AgentOrchestrator(db)
    result = await orchestrator.process(
        req.message, user_id=user_id, history=req.history
    )
    reply = _strip_tool_tags(result["reply"])
    return {
        "reply": reply,
        "intent": result.get("intent", "other"),
        "books": result.get("books"),
    }


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE 流式问答接口

    先用 process() 处理工具调用并提交事务（确保数据持久化），
    然后将回复文本通过 SSE 流式输出。
    """
    user_id = int(payload["sub"])
    orchestrator = AgentOrchestrator(db)
    result = await orchestrator.process(
        req.message, user_id=user_id, history=req.history
    )
    # 显式提交事务（解决 streaming 上下文中 session commit 不生效的问题）
    try:
        db.commit()
    except Exception:
        db.rollback()

    reply = result.get("reply", "")
    intent = result.get("intent", "other")

    # 兜底清理回复中的 DSML/XML 标记
    reply = _strip_tool_tags(reply)

    async def event_stream():
        # 逐字流式输出回复
        for i in range(0, len(reply), 2):
            chunk = reply[i:i+2]
            yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'content': reply, 'intent': intent}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
