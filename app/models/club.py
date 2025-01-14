# app/models/club.py
import string
import random
from datetime import datetime, timezone
from app.extensions import db

def generate_uid(length: int = 6) -> str:
    """ generate a random alphanumeric code for club unique_id """
    chars = string.ascii_uppercase + string.digits
    while True:
        uid = "".join(random.choice(chars) for _ in range(length))
        # make sure uid is not already in use
        existing = Club.query.filter_by(unique_id=uid).first()
        if not existing:
            return uid

class Club(db.Model):
    __tablename__ = "clubs"

    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(10), unique=True, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __init__(self, creator_id: int):
        self.creator_id = creator_id
        self.unique_id = generate_uid()

    def __repr__(self) -> str:
        return f"<Club {self.unique_id} (creator={self.creator_id})>"
