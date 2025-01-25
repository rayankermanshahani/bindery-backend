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

def emit_error(sid, message, code=400):
    """
    helper to send standardized error messages
    """
    socketio.emit("error", {"code": code, "message": message}, to=sid)

@socketio.on("connect")
def handle_conn():
    """
    handle new WebSocket connection
    """
    # handshake token check
    token = request.args.get("token")
    if token:
        user_id = authenticate_socket_conn(token)
        if not user_id:
            emit_error(request.sid, "Missing authentication token", 401)
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
    handle joining a book discussion room
    """
    token = data.get("token")
    book_id = data.get("book_id")
    sid = request.sid

    if not token or not book_id:
        emit_error(sid, "Missing token or book_id", 400)
        return

    user_id = authenticate_socket_conn(token)
    if not user_id:
        emit_error(sid, "Authentication failed", 401)
        return

    # validate book existence
    book = Book.query.get(book_id)
    if not book:
        emit_error(sid, "Book not found", 404)
        return

    # check club membership status
    membership = ClubMembership.query.filter_by(
        club_id=book.club_id,
        user_id=user_id,
        is_banned=False
    ).first()

    if not membership:
        emit_error(sid, "Not a member or banned from club", 403)
        return

    # success
    join_room(f"book_{book_id}")
    print(f"User {user_id} joined room book_{book_id}")
    socketio.emit("joined_room", {"room": f"book_{book_id}"}, to=sid)

@socketio.on("leave_book")
def handle_leave_book(data):
    """
    handle leaving a book discussion room
    """
    token = data.get("token")
    book_id = data.get("book_id")
    sid = request.sid

    if not token or not book_id:
        emit_error(sid, "Missing token or book_id", 400)
        return

    user_id = authenticate_socket_conn(token)
    if not user_id:
        emit_error(sid, "Authentication failed", 401)
        return

    leave_room(f"book_{book_id}")
    print(f"User {user_id} left room book_{book_id}")
    socketio.emit("left_room", {"room": f"book_{book_id}"}, to=sid)
