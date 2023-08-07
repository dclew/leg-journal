from app import create_app
from app.models import User, Trade, Order, Portfolio, Image
from flask_login import current_user

config_class = "config.DevelopmentConfig"
app = create_app(config_class)


@app.context_processor
def inject_variables():
    return dict()


if __name__ == "__main__":
    app.run(host="0.0.0.0")
