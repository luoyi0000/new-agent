from app.repositories.base import BaseRepository
from app.models.book import Book
from typing import Optional, List


class BookRepository(BaseRepository):
    def create_book(self, title: str, author: Optional[str] = None, isbn: Optional[str] = None,
                    category: Optional[str] = None, description: Optional[str] = None) -> int:
        book = Book(title=title, author=author, isbn=isbn, category=category, description=description)
        return self.add(book)

    def get_by_id(self, book_id: int) -> Optional[Book]:
        return self.db.query(Book).filter(Book.id == book_id).first()

    def search_by_title(self, keyword: str) -> List[Book]:
        return self.db.query(Book).filter(Book.title.ilike(f"%{keyword}%")).all()

    def search_by_category(self, category: str) -> List[Book]:
        return self.db.query(Book).filter(Book.category == category).all()

    def get_all(self) -> List[Book]:
        return self.db.query(Book).all()
