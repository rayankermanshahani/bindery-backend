from app.extensions import db
from datetime import datetime, timezone

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default= lambda: datetime.now(timezone.utc))

    def __init__(self, google_id: str, username: str) -> None:
        self.google_id = google_id
        self.username = username

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    @staticmethod
    def create_or_update(google_id: str, username: str):
        user = User.query.filter_by(google_id=google_id).first()
        if user:
            user.username = username
        else:
            user = User(google_id=google_id, username=username)
            db.session.add(user)
        db.session.commit()
        return user

