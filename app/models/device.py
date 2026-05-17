from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime, timezone
from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    device_type = Column(String(50), nullable=False)  # 3d_printer / vr / scanner
    location = Column(String(100), nullable=True)
    status = Column(String(20), default="available")  # available / in_use / maintenance
    hourly_rate = Column(Float, default=0.0)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
