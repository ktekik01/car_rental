from flask import Flask
from app.config import Config
from app.extensions import db, migrate
from routes.cars      import cars_bp
from routes.rentals   import rentals_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # register blueprints
    app.register_blueprint(cars_bp)
    app.register_blueprint(rentals_bp)

    return app

if __name__ == '__main__':
    create_app().run(debug=True)
