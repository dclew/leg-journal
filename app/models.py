from datetime import datetime
from app import db


class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    instrument = db.Column(db.String(30), nullable=False)
    open_date = db.Column(db.Date, nullable=False)
    orders = db.relationship("Order", backref="trade", lazy=True)

    def __repr__(self):
        return f"<Trade {self.symbol} - {self.instrument}>"

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "instrument": self.instrument,
            "open_date": str(self.open_date),
            "orders": [order.to_dict() for order in self.orders],
        }

    @property
    def status(self):
        total_quantity = 0
        total_cost = 0

        for order in self.orders:
            if order.quantity > 0:  # buy order
                total_quantity += order.quantity
                total_cost += order.total_cost
            elif order.quantity < 0:  # sell order
                total_quantity -= abs(order.quantity)
                total_cost -= order.total_cost

        if total_quantity != 0:  # still open
            return "open"
        elif total_cost < 0:  # win
            return "win"
        elif total_cost > 0:  # loss
            return "loss"

    @property
    def adjusted_cost(self):
        total_cost = 0
        for order in self.orders:
            if order.quantity > 0:  # Buy order
                total_cost += abs(order.total_cost)
        return total_cost

    @property
    def adjusted_proceeds(self):
        total_proceeds = 0
        for order in self.orders:
            if order.quantity < 0:  # Sell order
                total_proceeds += abs(order.total_cost)
        return total_proceeds

    @property
    def pnl(self):
        return self.adjusted_proceeds - self.adjusted_cost

    @property
    def pnl_percent(self):
        return round((self.pnl / self.adjusted_cost) * 100, 2)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    trade_id = db.Column(db.Integer, db.ForeignKey("trade.id"), nullable=False)

    @property
    def total_cost(self):
        return (self.price * self.quantity * 100) * -1

    def is_buy_order(self):
        return self.quantity > 0

    def is_sell_order(self):
        return self.quantity < 0

    @property
    def adjusted_cost(self):
        if self.is_buy_order():
            return self.total_cost
        else:
            return None

    @property
    def adjusted_proceeds(self):
        if self.is_sell_order():
            return self.total_cost
        else:
            return None

    @property
    def gross_pnl(self):
        if self.quantity < 0:  # Sell order
            buy_orders = [order for order in self.trade.orders if order.quantity > 0]
            total_quantity_bought = sum([order.quantity for order in buy_orders])
            if total_quantity_bought > 0:
                avg_buy_price = (
                    sum([order.price * order.quantity for order in buy_orders])
                    / total_quantity_bought
                )
                return round((self.price - avg_buy_price) * abs(self.quantity) * 100, 2)
            else:
                return None
        else:
            return None
