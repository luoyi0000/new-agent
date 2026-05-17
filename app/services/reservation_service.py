from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.seat_repository import SeatRepository
from app.repositories.policy_repository import PolicyRepository
from sqlalchemy.orm import Session


class ReservationService:
    def __init__(self, db: Session):
        self.repo = AppointmentRepository(db)
        self.seat_repo = SeatRepository(db)

    def get_user_appointments(self, user_id: int):
        return self.repo.get_by_user(user_id)

    def cancel(self, appointment_id: int, user_id: int) -> bool:
        apt = self.repo.get_by_id(appointment_id)
        if not apt or apt.user_id != user_id:
            return False
        apt.status = "cancelled"
        # 恢复座位状态为可用
        if apt.resource_type == "seat":
            seat = self.seat_repo.get_by_id(apt.resource_id)
            if seat:
                seat.status = "available"
        self.repo.db.commit()
        return True


class PolicyService:
    def __init__(self, db: Session):
        self.repo = PolicyRepository(db)

    def search(self, keyword: str):
        return self.repo.search(keyword)

    def get_by_category(self, category: str):
        return self.repo.search_by_category(category)
