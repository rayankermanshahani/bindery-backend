# app/models/message.py
from app.extensions import db
from datetime import datetime, timezone

class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __init__(self, book_id: int, user_id: int, content: str) -> None:
        self.book_id = book_id
        self.user_id = user_id
        self.content = content

    def __repr__(self) -> str:
        return f"<Message {self.id} by User {self.user_id}>"

