from flask import Flask
from .config import Config
from .extensions import db, migrate, api
from .auth.resources import LoginResource, UserProfileResource

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # add resources
    api.add_resource(LoginResource, "/auth/login")
    api.add_resource(UserProfileResource, "/auth/profile")
    api.init_app(app)

    return app
