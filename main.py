from app import create_app, db
from app.models import Trade, Order
from datetime import datetime, date

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "Trade": Trade,
        "Order": Order,
        "datetime": datetime,
        "date": date,
    }
