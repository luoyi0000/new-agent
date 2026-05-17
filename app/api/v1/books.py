"""馆藏检索 API"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.book_service import BookService

router = APIRouter(prefix="/books", tags=["馆藏检索"])


@router.get("/")
def list_books(
    query: str = Query("", description="搜索关键词"),
    category: str = Query(None, description="分类筛选"),
    db: Session = Depends(get_db),
):
    """检索图书（支持关键词 + 分类混合检索）"""
    service = BookService(db)
    if query or category:
        return {"items": service.search_books(query, category)}
    return {"items": service.get_all()}


@router.get("/{book_id}")
def get_book(book_id: int, db: Session = Depends(get_db)):
    """获取图书详情"""
    service = BookService(db)
    book = service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    return book
