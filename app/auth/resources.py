# app/auth/resources.py
from flask_restful import Resource, reqparse
from flask import current_app, request, g
from app.models.user import User
from app.extensions import db
from functools import wraps
import jwt
from datetime import datetime, timezone, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "Missing Authorization header"}, 401
        try:
            token = auth_header.split(" ")[1] # Bearer <token>
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
            g.user_id = payload["user_id"]
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError) as e:
            return {"error": str(e)}, 401
        except IndexError:
            return {"error": "Invalid Authorization header format"}, 401

        return f(*args, **kwargs)
    return decorated

class LoginResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("credential", type=str, required=True, help="Google OAuth credential is required")
        args = parser.parse_args()

        try:
            # verify google oauth token
            idinfo = id_token.verify_oauth2_token(
                args["credential"],
                google_requests.Request(),
                current_app.config["GOOGLE_CLIENT_ID"]
            )

            # get user info from token
            google_id = idinfo["sub"]
            email = idinfo["email"]
            # use email as initial username (can be changed later)
            username = email.split("@")[0]
            user = User.create_or_update(google_id, username)

            # create expiration time
            exp = datetime.now(timezone.utc) + timedelta(days=1)

            # create JWT
            jwt_token = jwt.encode(
                {
                    "user_id": user.id,
                    "exp": exp.timestamp()
                },
                current_app.config["SECRET_KEY"],
                algorithm="HS256"
            )

            return {
                "token": jwt_token,
                "user_id": user.id,
                "username": user.username,
            }

        except ValueError as e:
            # invalid token
            return {"error": "Invalid token"}, 401
        except Exception as e:
            return {"error": str(e)}, 400

class UserProfileResource(Resource):
    @jwt_required
    def get(self):
        """ get user profile """
        user = User.query.get(g.user_id)
        if not user:
            return {"error": "User not found"}, 404

        return {
            "id": user.id,
            "username": user.username,
            "created_at": user.created_at.isoformat()
        }

    @jwt_required
    def put(self):
        """ update user profile """
        parser = reqparse.RequestParser()
        parser.add_argument("username", type=str, required=True, help="Username is required")
        args = parser.parse_args()

        # validate username
        if len(args["username"]) < 3 or len(args["username"]) >= 49:
            return {"error": "Username must be between 3 and 49 characters"}, 400

        # check username availability
        existing_user = User.query.filter_by(username=args["username"]).first()
        if existing_user and existing_user.id != g.user_id:
            return {"error": "Username already taken"}, 400

        user = User.query.get(g.user_id)
        if not user:
            return {"error": "User not found"}, 404

        user.username = args["username"]
        db.session.commit()

        return {
            "id": user.id,
            "username": user.username,
            "created_at": user.created_at.isoformat()
        }

