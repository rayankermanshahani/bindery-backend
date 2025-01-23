from flask_restful import Resource
from flask import g
from app.auth.resources import jwt_required
from app.models.club_membership import ClubMembership
from app.models.book import Book
from app.models.message import Message

class MessageResource(Resource):
    @jwt_required
    def get(self, book_id: int): 
        """
        retrieve messages for a book
        """
        book = Book.query.get(book_id)
        if not book: return {"error": "Book not found"}, 404

        membership = ClubMembership.query.filter_by(
            club_id=book.club_id,
            user_id=g.user_id,
            is_banned=False
        ).first()

        if not membership or membership.is_banned:
            return {"error": "You are not an active member of this club"}, 403

        messages = Message.query.filter_by(book_id=book_id).order_by(Message.created_at.asc()).all()

        return [{
            "id": msg.id,
            "user_id": msg.user_id,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        } for msg in messages], 200

