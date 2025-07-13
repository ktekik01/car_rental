from flask import Flask
from app.config import Config
from flask_migrate import Migrate
from app.extensions import db, migrate


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # init db + migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # register all blueprints
    from app.routes import cars_bp, rentals_bp
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(cars_bp,   url_prefix="/cars")
    app.register_blueprint(rentals_bp, url_prefix="/rentals")

    return app
