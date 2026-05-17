from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone
from app.core.database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(200), nullable=True)
    isbn = Column(String(20), unique=True, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    location = Column(String(50), nullable=True)  # 馆藏位置, 如 "3F-A区-12架"
    status = Column(String(20), default="available")  # available / borrowed / reserved
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
