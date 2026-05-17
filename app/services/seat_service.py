from app.repositories.seat_repository import SeatRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.core.redis_client import get_redis
from app.core.database import SessionLocal
from sqlalchemy.orm import Session
from datetime import datetime


class SeatService:
    def __init__(self, db: Session):
        self.seat_repo = SeatRepository(db)
        self.apt_repo = AppointmentRepository(db)

    def get_available(self, floor: str = None):
        return self.seat_repo.get_available(floor)

    def get_by_floor(self, floor: str):
        return self.seat_repo.get_by_floor(floor)

    async def book_seat(self, user_id: int, seat_id: int, start_time: datetime, end_time: datetime) -> dict:
        seat = self.seat_repo.get_by_id(seat_id)
        if not seat:
            return {"status": "error", "message": "座位不存在"}

        if seat.status != "available":
            return {"status": "occupied", "message": "该座位已被占用"}

        # Redis 分布式锁
        redis = await get_redis()
        lock_key = f"seat_lock:{seat_id}:{start_time.isoformat()}"
        locked = await redis.set(lock_key, str(user_id), nx=True, ex=300)
        if not locked:
            return {"status": "occupied", "message": "该时段座位已被预约"}

        try:
            # 冲突检测
            conflicts = self.apt_repo.get_conflicts("seat", seat_id, start_time, end_time)
            if conflicts:
                await redis.delete(lock_key)
                return {"status": "conflict", "message": "该时段已有预约冲突"}

            # 创建预约
            apt_id = self.apt_repo.create(user_id, "seat", seat_id, start_time, end_time)
            seat.status = "reserved"
            self.apt_repo.db.commit()  # 立即提交，确保数据持久化
            return {"status": "success", "appointment_id": apt_id}
        finally:
            await redis.delete(lock_key)

    async def book_seat_independent(self, user_id: int, seat_id: int,
                                     start_time: datetime, end_time: datetime) -> dict:
        """使用独立数据库连接预约座位（解决 StreamingResponse 事务不提交的问题）"""
        db = SessionLocal()
        try:
            seat_repo = SeatRepository(db)
            apt_repo = AppointmentRepository(db)

            seat = seat_repo.get_by_id(seat_id)
            if not seat:
                return {"status": "error", "message": "座位不存在"}
            if seat.status != "available":
                return {"status": "occupied", "message": "该座位已被占用"}

            conflicts = apt_repo.get_conflicts("seat", seat_id, start_time, end_time)
            if conflicts:
                return {"status": "conflict", "message": "该时段已有预约冲突"}

            apt_id = apt_repo.create(user_id, "seat", seat_id, start_time, end_time)
            seat.status = "reserved"
            db.commit()
            db.refresh(seat)
            return {"status": "success", "appointment_id": apt_id}
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            db.close()
