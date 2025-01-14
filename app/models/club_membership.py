# app/models/club_membership.py
from datetime import datetime, timezone
from app.extensions import db

class ClubMembership(db.Model):
    __tablename__ = "club_memberships"

    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<ClubMembership club={self.club_id} user={self.user_id} banned={self.is_banned}>"
