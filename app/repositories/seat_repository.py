from app.repositories.base import BaseRepository
from app.models.seat import Seat
from typing import Optional, List


class SeatRepository(BaseRepository):
    def create_seat(self, code: str, floor: str, zone: Optional[str] = None, seat_type: str = "standard") -> int:
        seat = Seat(code=code, floor=floor, zone=zone, seat_type=seat_type)
        return self.add(seat)

    def get_by_id(self, seat_id: int) -> Optional[Seat]:
        return self.db.query(Seat).filter(Seat.id == seat_id).first()

    def get_all(self) -> List[Seat]:
        return self.db.query(Seat).all()

    def get_by_floor(self, floor: str) -> List[Seat]:
        return self.db.query(Seat).filter(Seat.floor == floor).all()

    def get_by_code(self, code: str) -> Optional[Seat]:
        return self.db.query(Seat).filter(Seat.code == code).first()

    def get_available(self, floor: Optional[str] = None) -> List[Seat]:
        query = self.db.query(Seat).filter(Seat.status == "available")
        if floor:
            query = query.filter(Seat.floor == floor)
        return query.all()
