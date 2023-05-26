from datetime import datetime, timedelta, date
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import desc


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    default_portfolio_id = db.Column(db.Integer)
    portfolios = db.relationship("Portfolio", backref="user", lazy=True)

    def __repr__(self):
        return "<User {}>".format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def default_portfolio_name(self):
        if self.default_portfolio_id:
            portfolio_name = Portfolio.query.get(self.default_portfolio_id)
            return portfolio_name.name


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    trades = db.relationship("Trade", backref="portfolio", lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    @property
    def pnl(self):
        pnl = 0
        if self.trades:
            for trade in self.trades:
                pnl += trade.pnl
        return pnl

    @property
    def profit_factor(self):
        if self.trades:
            if self.num_losing_trades > 0:
                profit_total = 0
                loss_total = 0
                for trade in self.trades:
                    if trade.status == "OPEN":
                        continue
                    elif trade.status == "WIN":
                        profit_total += trade.pnl
                    elif trade.status == "LOSS":
                        loss_total += trade.pnl
                return round(profit_total / abs(loss_total), 2)
        else:
            return "---"

    @property
    def total_profit(self):
        total_profit = 0
        for trade in self.trades:
            if trade.status == "WIN":
                total_profit += trade.pnl
        return total_profit

    @property
    def total_losses(self):
        total_losses = 0
        for trade in self.trades:
            if trade.status == "LOSS":
                total_losses += trade.pnl
        return total_losses

    @property
    def average_winning_profit(self):
        winning_profits = [trade.pnl for trade in self.trades if trade.status == "WIN"]
        if winning_profits:
            return round(sum(winning_profits) / len(winning_profits), 2)
        else:
            return 0

    @property
    def average_losing_profit(self):
        losing_profits = [trade.pnl for trade in self.trades if trade.status == "LOSS"]
        if losing_profits:
            return round(sum(losing_profits) / len(losing_profits), 2)
        else:
            return 0

    @property
    def average_win_loss_trade(self):
        if self.trades:
            if self.average_losing_profit:
                return abs(
                    round(self.average_winning_profit / self.average_losing_profit, 2)
                )

    @property
    def win_percentage(self):
        total_trades = len(self.trades)
        if total_trades == 0:
            return 0

        winning_trades = [trade for trade in self.trades if trade.status == "WIN"]
        num_winning_trades = len(winning_trades)
        return round((num_winning_trades / total_trades) * 100, 2)

    @property
    def num_winning_trades(self):
        winning_trades = [trade for trade in self.trades if trade.status == "WIN"]
        return len(winning_trades)

    @property
    def num_losing_trades(self):
        losing_trades = [trade for trade in self.trades if trade.status == "LOSS"]
        return len(losing_trades)

    @property
    def num_closed_trades(self):
        trades = [trade for trade in self.trades if trade.status != "OPEN"]
        return len(trades)

    @property
    def trade_expectancy(self):
        return round(
            self.average_winning_profit * (self.win_percentage / 100)
            - abs(self.average_losing_profit * ((100 - self.win_percentage) / 100)),
            2,
        )

    @property
    def avg_time_in_trade(self):
        trades = [
            trade
            for trade in self.trades
            if trade.status != "OPEN" and trade.time_in_trade is not None
        ]
        total_time_in_trade = sum(trade.time_in_trade for trade in trades)
        num_trades = len(trades)
        if num_trades > 0:
            return round(total_time_in_trade / num_trades, 2)
        else:
            return None

    @property
    def avg_time_in_trade_winning_trades(self):
        winning_trades = [trade for trade in self.trades if trade.status == "WIN"]
        total_time_in_trade = sum(
            trade.time_in_trade
            for trade in winning_trades
            if trade.time_in_trade is not None
        )
        num_winning_trades = len(winning_trades)
        if num_winning_trades > 0:
            return round(total_time_in_trade / num_winning_trades, 2)
        else:
            return None

    @property
    def avg_time_in_trade_losing_trades(self):
        losing_trades = [trade for trade in self.trades if trade.status == "LOSS"]
        total_time_in_trade = sum(
            trade.time_in_trade
            for trade in losing_trades
            if trade.time_in_trade is not None
        )
        num_losing_trades = len(losing_trades)
        if num_losing_trades > 0:
            return round(total_time_in_trade / num_losing_trades, 2)
        else:
            return None

    def calculate_pnl_over_time(self, start_date, end_date):
        pnl = 0

        for trade in self.trades:
            trade_date = trade.date_time.date()
            if start_date <= trade_date <= end_date:
                pnl += trade.pnl

        return pnl

    def calculate_pnl_over_time(self, start_date, end_date):
        pnl_over_time = {}

        current_date = start_date
        pnl_sum = 0  # Cumulative PNL sum

        # Find trades within the specified date range
        trades_within_range = [
            trade
            for trade in self.trades
            if start_date <= trade.date_time.date() <= end_date
        ]

        while current_date <= end_date:
            # Calculate the PNL for trades up to the current date and update the cumulative PNL
            trades_up_to_date = [
                trade
                for trade in trades_within_range
                if trade.date_time.date() <= current_date
            ]
            pnl_sum = sum(trade.pnl for trade in trades_up_to_date)

            pnl_over_time[
                current_date
            ] = pnl_sum  # Store the cumulative PNL for the current date

            current_date += timedelta(days=1)  # Move to the next day

        return pnl_over_time

    def calculate_cumulative_pnl(self, start_date=None, end_date=None):
        if start_date is None:
            start_date = self.get_first_trade_date()
        if end_date is None:
            end_date = self.get_last_trade_date()

        # Adjust start_date and end_date to date objects
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        cumulative_pnl = {}
        pnl_sum = 0.0
        trades = sorted(
            filter(lambda trade: trade.status != "OPEN", self.trades),
            key=lambda trade: trade.close_date,
        )
        for trade in trades:
            trade_date = trade.close_date.date()
            if start_date <= trade_date <= end_date:
                if trade_date not in cumulative_pnl:
                    cumulative_pnl[trade_date] = 0.0
                pnl_sum += trade.pnl
                cumulative_pnl[trade_date] = pnl_sum

        return cumulative_pnl

    def calculate_daily_pnl(self):
        daily_pnl = {}
        trades = sorted(
            filter(lambda trade: trade.status != "OPEN", self.trades),
            key=lambda trade: trade.close_date,
        )
        for trade in trades:
            trade_date = trade.close_date.date()
            if trade_date not in daily_pnl:
                daily_pnl[trade_date] = 0.0
            daily_pnl[trade_date] += trade.pnl

        return daily_pnl

    def get_first_trade_date(self):
        first_trade = (
            Trade.query.filter_by(portfolio_id=self.id)
            .order_by(Trade.date_time.asc())
            .first()
        )
        if first_trade:
            return first_trade.date_time.date().strftime("%Y-%m-%d")
        return date.today().strftime("%Y-%m-%d")

    def get_last_trade_date(self):
        last_trade = (
            Trade.query.filter_by(portfolio_id=self.id)
            .order_by(Trade.date_time.desc())
            .first()
        )
        if last_trade:
            return last_trade.date_time.date().strftime("%Y-%m-%d")
        return date.today().strftime("%Y-%m-%d")

    @property
    def has_open_trades(self):
        for trade in self.trades:
            if trade.status == "OPEN":
                return True
        return False


class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    market = db.Column(db.String(15), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    instrument = db.Column(db.String(30), nullable=False)
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    trade_notes = db.Column(db.Text, default="")
    orders = db.relationship("Order", backref="trade", cascade="all, delete", lazy=True)
    images = db.relationship("Image", backref="trade", cascade="all, delete", lazy=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolio.id"), nullable=False)

    def __repr__(self):
        return f"<Trade {self.symbol} - {self.instrument}>"

    def to_dict(self):
        return {
            "id": self.id,
            "market": self.market,
            "symbol": self.symbol,
            "instrument": self.instrument,
            "status": self.status,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "date_time": str(self.date_time),
            "adjusted_cost": self.adjusted_cost,
            "trade_notes": self.trade_notes,
            "orders": [order.to_dict() for order in self.orders],
            "images": [image.to_dict() for image in self.images],
            "portfolio_id": self.portfolio_id,
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
            return "OPEN"
        elif self.pnl > 0:  # win
            return "WIN"
        elif self.pnl < 0:  # loss
            return "LOSS"

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
        if self.volume > 0:
            return 0
        else:
            return self.adjusted_proceeds - self.adjusted_cost

    @property
    def pnl_percent(self):
        if self.adjusted_cost > 0:
            return round((self.pnl / self.adjusted_cost) * 100, 2)
        else:
            return 0

    @property
    def volume(self):
        total_quantity = sum(order.quantity for order in self.orders)
        return total_quantity

    @property
    def formatted_date_time(self):
        return self.date_time.strftime("%a, %b %d, %Y")

    @property
    def time_in_trade(self):
        if self.status != "OPEN":
            open_time = self.date_time
            close_time = self.orders[-1].date_time
            time_diff = close_time - open_time
            return time_diff.total_seconds() // 60  # Return time in minutes
        else:
            return None

    @property
    def close_date(self):
        if self.status != "OPEN":
            last_close_order = self.orders[-1]
            return last_close_order.date_time
        else:
            return None


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    trade_id = db.Column(db.Integer, db.ForeignKey("trade.id"), nullable=False)

    def __repr__(self):
        return f"<Image {self.filename}>"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    trade_id = db.Column(db.Integer, db.ForeignKey("trade.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "date_time": str(self.date_time),
            "price": self.price,
            "quantity": self.quantity,
            "trade_id": self.trade_id,
        }

    @property
    def total_cost(self):
        if self.trade.market == "Options":
            cost = round(abs(self.price * self.quantity * 100), 2)
        else:
            cost = round(abs(self.price * self.quantity), 2)
        return cost

    def is_buy_order(self):
        return self.quantity > 0

    def is_sell_order(self):
        return self.quantity < 0

    @property
    def buy_sell(self):
        if self.quantity > 0:
            return "Buy"
        elif self.quantity < 0:
            return "Sell"
        else:
            return "Unknown"

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
                if self.trade.market == "Options":
                    return round(
                        (self.price - avg_buy_price) * abs(self.quantity) * 100, 2
                    )
                else:
                    return round((self.price - avg_buy_price) * abs(self.quantity), 2)
            else:
                return None
        else:
            return None

    @property
    def formatted_date_time(self):
        return self.date_time.strftime("%Y-%m-%d %H:%M")
