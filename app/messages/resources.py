# app/messages/resources.py
from flask_restful import Resource, reqparse
from flask import g
from app.extensions import db, socketio
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

        if not membership:
            return {"error": "You are not an active member of this club"}, 403

        messages = Message.query.filter_by(book_id=book_id).order_by(Message.created_at.asc()).all()

        return [{
            "id": msg.id,
            "user_id": msg.user_id,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        } for msg in messages], 200

    @jwt_required
    def post(self, book_id: int):
        """
        create a new message in a book's discussion
        """
        parser = reqparse.RequestParser()
        parser.add_argument("content", type=str, required=True, help="Message content is required")
        args = parser.parse_args()

        book = Book.query.get(book_id)
        if not book: return {"error": "Book not found"}, 404

        # check membership
        membership = ClubMembership.query.filter_by(
            club_id=book.club_id,
            user_id=g.user_id,
            is_banned=False
        ).first()

        if not membership:
            return {"error": "You are not an active member of this club"}, 403

        # create and store message
        new_message = Message(
            book_id=book_id,
            user_id=g.user_id,
            content=args["content"],
        )
        db.session.add(new_message)
        db.session.commit()

        # broadcast message via socketio
        socketio.emit(
            "new_message",
            {
                "id": new_message.id,
                "book_id": new_message.book_id,
                "user_id": new_message.user_id,
                "content": new_message.content,
                "created_at": new_message.created_at.isoformat()
            },
            to=f"book_{book_id}"
        )

        return {
            "id": new_message.id,
            "book_id": new_message.book_id,
            "user_id": new_message.user_id,
            "content": new_message.content,
            "created_at": new_message.created_at.isoformat()
        }, 201

