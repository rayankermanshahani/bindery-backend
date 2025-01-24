# app/sockets.py
from flask import current_app, request
from flask_socketio import disconnect, join_room, leave_room
import jwt
from app.extensions import db, socketio
from app.models.user import User
from app.models.book import Book
from app.models.club_membership import ClubMembership

def authenticate_socket_conn(token: str):
    """
    decode JWT from client and return user_id if valid, else None.
    raise exception or return None if invalid.
    """

    try:
        payload = jwt.decode(
            token, 
            current_app.config["SECRET_KEY"], 
            algorithms=["HS256"]
        )
        return payload["user_id"]
    except Exception:
        return None

@socketio.on("connect")
def handle_conn():
    """
    handle new WebSocket connection, allowed by default but do not
    join any rooms until client emits a `join_book` event.
    """
    # handshake token check
    token = request.args.get("token")
    if token:
        user_id = authenticate_socket_conn(token)
        if not user_id:
            disconnect()
    print("Socket connected")

@socketio.on("disconnect")
def handle_disconnect():
    """
    handle a client disconnecting
    """
    print("Socket disconnected")

@socketio.on("join_book")
def handle_join_book(data):
    """
    custom event client can emit to join a room for a particular
    book's discussoin.

    data format example: {"token": "...", "book_id": 123} 
    """

    token = data.get("token")
    book_id = data.get("book_id")

    if not token or not book_id:
        return # TODO: emit error event

    user_id = authenticate_socket_conn(token)
    if not user_id:
        return # TODO: emit error event or forcibly disconnect

    # check membership
    book = Book.query.get(book_id)
    if not book:
        return # book does not exist

    membership = ClubMembership.query.filter_by(
        club_id=book.club_id,
        user_id=user_id,
        is_banned=False
    ).first()

    if not membership:  
        return # TODO: emit error event

    join_room(f"book_{book_id}")
    print(f"User {user_id} joined room book_{book_id}")

    # emit a "joined_room" event back to user
    socketio.emit("joined_room", {f"book_{book_id}"}, to=request.sid)

@socketio.on("leave_book")
def handle_leave_book(data):
    """
    let users explicitly leave the room for a book discussion.
    client can emit: {"token": "...", "book_id": 123}
    """
    token = data.get("token")
    book_id = data.get("book_id")

    if not token or not book_id:
        return # TODO: emit error event

    user_id = authenticate_socket_conn(token)
    if not user_id:
        return # TODO: emit error event

    leave_room(f"book_{book_id}")
    print(f"User {user_id} left room book_{book_id}")
