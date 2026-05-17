from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any


class BaseRepository:
    """基础 Repository，提供通用 CRUD 操作"""

    def __init__(self, db: Session):
        self.db = db

    def add(self, obj) -> int:
        self.db.add(obj)
        self.db.flush()
        return obj.id

    def delete(self, obj) -> bool:
        self.db.delete(obj)
        return True
