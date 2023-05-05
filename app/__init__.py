from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()
migrate = Migrate()
config_class = "config.DevelopmentConfig"


def create_app(config_class=config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.trades.views import trades_bp
    from app.views import default_bp

    app.register_blueprint(trades_bp)
    app.register_blueprint(default_bp)

    return app


from app import models
