from app import create_app, db
from app.models import Trade, Order, Portfolio, Image, User
from datetime import datetime, date

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Portfolio": Portfolio,
        "Trade": Trade,
        "Order": Order,
        "Image": Image,
        "datetime": datetime,
        "date": date,
    }
