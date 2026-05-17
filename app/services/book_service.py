from app.repositories.book_repository import BookRepository
from sqlalchemy.orm import Session


class BookService:
    def __init__(self, db: Session):
        self.repo = BookRepository(db)

    def search_books(self, query: str, category: str = None):
        results = self.repo.search_by_title(query)
        if category:
            cat_results = self.repo.search_by_category(category)
            results = list({b.id: b for b in results + cat_results}.values())
        return results

    def get_book(self, book_id: int):
        return self.repo.get_by_id(book_id)

    def get_all(self):
        return self.repo.get_all()
