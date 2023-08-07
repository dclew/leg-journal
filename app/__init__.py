from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
config_class = "config.DevelopmentConfig"
login = LoginManager()
login.login_view = "auth_bp.login"


def create_app(config_class=config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    CSRFProtect(app)

    from app.trades.views import trades_bp
    from app.views import default_bp
    from app.auth.views import auth_bp
    from app.users.views import users_bp

    app.register_blueprint(trades_bp)
    app.register_blueprint(default_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)

    return app


from app import models
