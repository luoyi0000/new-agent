"""预约管理 API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.seat import Seat
from app.services.reservation_service import ReservationService

router = APIRouter(prefix="/appointments", tags=["预约管理"])


@router.get("/")
def list_appointments(
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的所有预约"""
    user_id = int(payload["sub"])
    service = ReservationService(db)
    items = service.get_user_appointments(user_id)

    # 补充资源编号（如座位 code）
    result = []
    for apt in items:
        data = {
            "id": apt.id,
            "user_id": apt.user_id,
            "resource_type": apt.resource_type,
            "resource_id": apt.resource_id,
            "start_time": apt.start_time,
            "end_time": apt.end_time,
            "status": apt.status,
            "version": apt.version,
            "created_at": apt.created_at,
        }
        if apt.resource_type == "seat":
            seat = db.query(Seat).filter(Seat.id == apt.resource_id).first()
            data["resource_code"] = seat.code if seat else str(apt.resource_id)
        else:
            data["resource_code"] = str(apt.resource_id)
        result.append(data)
    return {"items": result}


@router.post("/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: int,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取消预约"""
    user_id = int(payload["sub"])
    service = ReservationService(db)
    success = service.cancel(appointment_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在或无权操作",
        )
    return {"message": "预约已取消"}
