from datetime import datetime, timedelta, date
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import desc
from collections import defaultdict


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    default_portfolio_id = db.Column(db.Integer)
    portfolios = db.relationship("Portfolio", backref="user", lazy=True)
    setups = db.relationship(
        "Setup", backref="user", cascade="all, delete", lazy="dynamic"
    )
    mistakes = db.relationship(
        "Mistake", backref="user", cascade="all, delete", lazy="dynamic"
    )

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
    trades = db.relationship(
        "Trade", backref="portfolio", cascade="all, delete", lazy=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    @property
    def pnl(self):
        pnl = 0
        if self.trades:
            for trade in self.trades:
                pnl += trade.pnl
        return pnl

    @property
    def open_pnl(self):
        pnl = 0
        if self.trades:
            for trade in self.trades:
                if trade.is_open:
                    pnl += trade.open_pnl
        return round(pnl, 2)

    @property
    def open_pnl_percent(self):
        if self.open_cost_proceed == 0:
            return 0
        return round((self.open_pnl / self.open_cost_proceed) * 100, 2)

    @property
    def open_cost_proceed(self):
        cost_proceed = 0
        if self.trades:
            for trade in self.trades:
                if trade.is_open:
                    if trade.is_credit:
                        cost_proceed += trade.adjusted_proceeds
                    elif trade.is_debit:
                        cost_proceed += trade.adjusted_cost
        return cost_proceed

    @property
    def open_mkt_value(self):
        mkt_value = 0
        if self.trades:
            for trade in self.trades:
                if trade.is_open:
                    mkt_value += trade.mkt_value
        return mkt_value

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

    def calculate_monthly_pnl(self):
        monthly_pnl = defaultdict(float)
        trades = sorted(
            filter(lambda trade: trade.status != "OPEN", self.trades),
            key=lambda trade: trade.close_date,
        )
        for trade in trades:
            trade_month = trade.close_date.month
            trade_year = trade.close_date.year
            trade_month_start = date(trade_year, trade_month, 1)
            if trade_month_start not in monthly_pnl:
                monthly_pnl[trade_month_start] = 0.0
            monthly_pnl[trade_month_start] += trade.pnl

        return monthly_pnl

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
    current_price = db.Column(db.Float)
    trade_notes = db.Column(db.Text, default="")
    orders = db.relationship("Order", backref="trade", cascade="all, delete", lazy=True)
    images = db.relationship("Image", backref="trade", cascade="all, delete", lazy=True)
    setups = db.relationship(
        "Setup", secondary="trade_setup", backref="trades", lazy=True
    )
    mistakes = db.relationship(
        "Mistake", secondary="trade_mistake", backref="trades", lazy=True
    )
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
    def api_symbol(self):
        if self.market == "Stock":
            return self.symbol
        elif self.market == "Options":
            option_contract = self.instrument
            ticker = self.symbol
            parts = option_contract.split(" ")
            expiration_date = datetime.strptime(parts[0], "%m-%d-%Y").strftime("%y%m%d")
            strike_price = float(parts[1]) * 1000
            strike_price = f"{strike_price:08.0f}"
            option_type = parts[2].upper()
            if option_type == "CALL":
                option_type = "C"
            elif option_type == "PUT":
                option_type = "P"

            contract = f"{ticker}{expiration_date}{option_type}{strike_price}"
            return contract

    @property
    def only_date(self):
        return self.date_time.date()

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
    def is_open(self):
        total_quantity = 0
        for order in self.orders:
            if order.quantity > 0:  # buy order
                total_quantity += order.quantity
            elif order.quantity < 0:  # sell order
                total_quantity -= abs(order.quantity)
        if total_quantity != 0:
            return True
        else:
            return False

    @property
    def is_credit(self):
        first_order = self.orders[0]
        if first_order.quantity < 0:
            return True

    @property
    def is_debit(self):
        first_order = self.orders[0]
        if first_order.quantity > 0:
            return True

    @property
    def avg_entry(self):
        quantity = 0
        price = 0
        if self.is_credit:
            for order in self.orders:
                if order.is_sell_order:
                    quantity += order.quantity
                    price += order.price * order.quantity
            avg_entry = price / quantity
            return round(abs(avg_entry), 2)
        if self.is_debit:
            for order in self.orders:
                if order.is_buy_order:
                    quantity += order.quantity
                    price += order.price * order.quantity
            avg_entry = price / quantity
            return round(avg_entry, 2)

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
        if self.is_open:
            return 0
        else:
            return self.adjusted_proceeds - self.adjusted_cost

    @property
    def open_pnl(self):
        multiplier = 1
        if self.is_open:
            if self.current_price:
                if self.market == "Options":
                    multiplier = 100
                if self.is_credit:
                    return round(
                        self.adjusted_proceeds
                        - (self.current_price * self.volume * multiplier),
                        2,
                    )
                if self.is_debit:
                    return round(
                        (self.current_price * self.volume * multiplier)
                        - self.adjusted_cost,
                        2,
                    )
        else:
            return 0

    @property
    def mkt_value(self):
        multiplier = 1
        if self.is_open:
            if self.current_price:
                if self.market == "Options":
                    multiplier = 100
                if self.is_credit:
                    return round((self.current_price * self.volume * multiplier), 2)
                if self.is_debit:
                    return round((self.current_price * self.volume * multiplier), 2)
        else:
            return 0

    @property
    def open_pnl_percent(self):
        if self.is_open:
            if self.current_price:
                if self.is_credit:
                    return round((self.open_pnl / self.adjusted_proceeds) * 100, 2)
                elif self.is_debit:
                    return round((self.open_pnl / self.adjusted_cost) * 100, 2)

    @property
    def pnl_percent(self):
        if self.is_credit:
            if self.adjusted_proceeds > 0:
                return round((self.pnl / self.adjusted_proceeds) * 100, 2)
            else:
                return 0
        elif self.is_debit:
            if self.adjusted_cost > 0:
                return round((self.pnl / self.adjusted_cost) * 100, 2)
            else:
                return 0

    @property
    def volume(self):
        total_quantity = sum(order.quantity for order in self.orders)
        return abs(total_quantity)

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


class Setup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


trade_setup = db.Table(
    "trade_setup",
    db.Column("trade_id", db.Integer, db.ForeignKey("trade.id"), primary_key=True),
    db.Column("setup_id", db.Integer, db.ForeignKey("setup.id"), primary_key=True),
)


class Mistake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


trade_mistake = db.Table(
    "trade_mistake",
    db.Column("trade_id", db.Integer, db.ForeignKey("trade.id"), primary_key=True),
    db.Column("mistake_id", db.Integer, db.ForeignKey("mistake.id"), primary_key=True),
)


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    trade_id = db.Column(db.Integer, db.ForeignKey("trade.id"), nullable=False)

    def __repr__(self):
        return f"<Image {self.filename}>"

    def to_dict(self):
        return {
            "id": self.id,
            "filename": str(self.filename),
            "trade_id": self.trade_id,
        }


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

    @property
    def is_buy_order(self):
        if self.quantity > 0:
            return True

    @property
    def is_sell_order(self):
        if self.quantity < 0:
            return True

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
        if self.is_buy_order:
            return self.total_cost
        else:
            return None

    @property
    def adjusted_proceeds(self):
        if self.is_sell_order:
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
