"""超时释放任务"""
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.seat_repository import SeatRepository
from datetime import datetime


@celery_app.task
def release_expired_appointments():
    """释放已过期的预约"""
    db = SessionLocal()
    try:
        apt_repo = AppointmentRepository(db)
        seat_repo = SeatRepository(db)
        now = datetime.utcnow()

        expired = apt_repo.db.query(apt_repo.model).filter(
            apt_repo.model.end_time <= now,
            apt_repo.model.status == "confirmed",
        ).all()

        for apt in expired:
            apt.status = "completed"
            if apt.resource_type == "seat":
                seat = seat_repo.get_by_id(apt.resource_id)
                if seat and seat.status == "reserved":
                    seat.status = "available"

        db.commit()
        return {"released": len(expired)}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
