from app.repositories.base import BaseRepository
from app.models.policy_doc import PolicyDoc
from typing import Optional, List


class PolicyRepository(BaseRepository):
    def create(self, title: str, content: str, category: Optional[str] = None) -> int:
        doc = PolicyDoc(title=title, content=content, category=category)
        return self.add(doc)

    def get_by_id(self, doc_id: int) -> Optional[PolicyDoc]:
        return self.db.query(PolicyDoc).filter(PolicyDoc.id == doc_id).first()

    def search_by_category(self, category: str) -> List[PolicyDoc]:
        return self.db.query(PolicyDoc).filter(PolicyDoc.category == category).all()

    def search(self, keyword: str) -> List[PolicyDoc]:
        return self.db.query(PolicyDoc).filter(
            PolicyDoc.title.ilike(f"%{keyword}%")
            | PolicyDoc.content.ilike(f"%{keyword}%")
            | PolicyDoc.category.ilike(f"%{keyword}%")
        ).all()

    def get_all(self) -> List[PolicyDoc]:
        return self.db.query(PolicyDoc).all()
