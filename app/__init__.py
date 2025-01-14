# app/__init__.py
from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate, api
from .auth.resources import (LoginResource, UserProfileResource)
from .clubs.resources import (
    ClubsListResource,
    ClubResource,
    ClubJoinResource,
    ClubLeaveResource,
    ClubBanResource
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # configure cors
    CORS(
        app, 
        resources={r"/*": {"origins": "http://localhost:5173"}}, 
        supports_credentials=True
    )

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # auth resources
    api.add_resource(LoginResource, "/auth/login")
    api.add_resource(UserProfileResource, "/auth/profile")

    # club resources
    api.add_resource(ClubsListResource, "/clubs")  # GET (list), POST (create)
    api.add_resource(ClubResource, "/clubs/<string:unique_id>")  # GET (detail), DELETE (delete)
    api.add_resource(ClubJoinResource, "/clubs/<string:unique_id>/join")
    api.add_resource(ClubLeaveResource, "/clubs/<string:unique_id>/leave")
    api.add_resource(ClubBanResource, "/clubs/<string:unique_id>/ban")

    api.init_app(app)

    return app
