from app import create_app
from app.models import User, Trade, Order, Portfolio, Image

config_class = "config.DevelopmentConfig"
app = create_app(config_class)


@app.context_processor
def inject_variables():
    nav_portfolios = Portfolio.query.all()
    return dict(nav_portfolios=nav_portfolios)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
