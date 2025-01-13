# app/__init__.py
from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate, api
from .auth.resources import LoginResource, UserProfileResource

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

    # add resources
    api.add_resource(LoginResource, "/auth/login")
    api.add_resource(UserProfileResource, "/auth/profile")
    api.init_app(app)

    return app
