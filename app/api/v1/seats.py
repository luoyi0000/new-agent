"""座位查询与预约 API"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.seat_service import SeatService

router = APIRouter(prefix="/seats", tags=["座位管理"])


@router.get("/")
def list_seats(
    floor: str = Query(None, description="楼层，如 3F/4F/5F"),
    db: Session = Depends(get_db),
):
    """按楼层查询座位"""
    service = SeatService(db)
    if floor:
        return {"items": service.get_by_floor(floor)}
    return {"items": service.get_available()}


@router.get("/available")
def available_seats(
    floor: str = Query(None, description="楼层筛选"),
    db: Session = Depends(get_db),
):
    """查询空闲座位"""
    service = SeatService(db)
    return {"items": service.get_available(floor)}


@router.post("/book")
async def book_seat(
    seat_id: int = Query(...),
    start_time: str = Query(..., description="开始时间 ISO 格式"),
    end_time: str = Query(..., description="结束时间 ISO 格式"),
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """预约座位（Redis 分布式锁防并发）"""
    user_id = int(payload["sub"])
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="时间格式错误")

    service = SeatService(db)
    result = await service.book_seat(user_id, seat_id, start, end)

    if result["status"] == "error":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])
    if result["status"] in ("occupied", "conflict"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result["message"])

    return {"appointment_id": result["appointment_id"], "message": "预约成功"}
