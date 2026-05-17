from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from datetime import datetime, timezone
from app.core.database import Base


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)  # 如 "3F-A12"
    floor = Column(String(10), nullable=False)  # 3F, 4F, 5F
    zone = Column(String(50), nullable=True)  # 静音区, 讨论区
    seat_type = Column(String(20), default="standard")  # standard / double / computer
    status = Column(String(20), default="available")  # available / occupied / reserved
    version = Column(Integer, default=1)  # 乐观锁版本号
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
