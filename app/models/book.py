# app/models/book.py
from app.extensions import db
from datetime import datetime, timezone

class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __init__(self, club_id: int, title: str, author: str) -> None:
        self.club_id = club_id
        self.title = title
        self.author = author

    def __repr__(self) -> str:
        return f"<Book {self.title} by {self.author}>"
