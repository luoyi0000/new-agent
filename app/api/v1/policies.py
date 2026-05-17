"""政策规则 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.policy_doc import PolicyDoc

router = APIRouter(prefix="/policies", tags=["政策规则"])


@router.get("/")
def list_policies(
    keyword: str = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
):
    """查询规则，可按关键词搜索"""
    q = db.query(PolicyDoc)
    if keyword:
        q = q.filter(
            PolicyDoc.title.ilike(f"%{keyword}%")
            | PolicyDoc.content.ilike(f"%{keyword}%")
            | PolicyDoc.category.ilike(f"%{keyword}%")
        )
    items = q.order_by(PolicyDoc.category, PolicyDoc.id).all()
    return {"items": items}
