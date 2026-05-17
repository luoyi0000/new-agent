from app.repositories.base import BaseRepository
from app.models.appointment import Appointment
from datetime import datetime
from typing import Optional, List


class AppointmentRepository(BaseRepository):
    def create(self, user_id: int, resource_type: str, resource_id: int,
               start_time: datetime, end_time: datetime) -> int:
        apt = Appointment(
            user_id=user_id, resource_type=resource_type, resource_id=resource_id,
            start_time=start_time, end_time=end_time,
        )
        return self.add(apt)

    def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        return self.db.query(Appointment).filter(Appointment.id == appointment_id).first()

    def get_by_user(self, user_id: int) -> List[Appointment]:
        return self.db.query(Appointment).filter(Appointment.user_id == user_id).order_by(Appointment.created_at.desc()).all()

    def get_conflicts(self, resource_type: str, resource_id: int,
                      start_time: datetime, end_time: datetime) -> List[Appointment]:
        return self.db.query(Appointment).filter(
            Appointment.resource_type == resource_type,
            Appointment.resource_id == resource_id,
            Appointment.status.in_(["pending", "confirmed"]),
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        ).all()
