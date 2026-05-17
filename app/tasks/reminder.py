"""预约提醒任务"""
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.repositories.appointment_repository import AppointmentRepository
from datetime import datetime, timedelta


@celery_app.task
def send_appointment_reminder():
    """发送预约开始前 30 分钟的提醒"""
    db = SessionLocal()
    try:
        repo = AppointmentRepository(db)
        now = datetime.utcnow()
        window_start = now + timedelta(minutes=30)
        window_end = now + timedelta(minutes=40)

        upcoming = repo.db.query(repo.model).filter(
            repo.model.start_time >= window_start,
            repo.model.start_time <= window_end,
            repo.model.status == "confirmed",
        ).all()

        for apt in upcoming:
            # TODO: 集成通知渠道（邮件/站内信/WebSocket）
            pass

        return {"reminded": len(upcoming)}
    finally:
        db.close()
