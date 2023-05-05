from app import db


class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    trade_date = db.Column(db.Date, nullable=False)
    entry_times = db.Column(db.String(255))
    entry_prices = db.Column(db.String(255))
    entry_contracts = db.Column(db.String(255))
    exit_times = db.Column(db.String(255))
    exit_prices = db.Column(db.String(255))
    exit_contracts = db.Column(db.String(255))
    image_path = db.Column(db.String(255))

    def __repr__(self):
        return f"<Trade {self.symbol} - {self.entry_contracts} contracts>"

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "trade_date": self.trade_date.isoformat(),
            "entry_times": self.entry_times.split(","),
            "entry_prices": [float(p) for p in self.entry_prices.split(",")],
            "entry_contracts": [int(c) for c in self.entry_contracts.split(",")],
            "exit_times": self.exit_times.split(","),
            "exit_prices": [float(p) for p in self.exit_prices.split(",")],
            "exit_contracts": [int(c) for c in self.exit_contracts.split(",")],
            "image_path": self.image_path,
        }

    def calculate_pnl(self):
        # Split the entry/exit prices and contracts by comma
        entry_prices = [float(price) * 100 for price in self.entry_prices.split(",")]
        entry_contracts = [
            int(contract) for contract in self.entry_contracts.split(",")
        ]
        exit_prices = [float(price) * 100 for price in self.exit_prices.split(",")]
        exit_contracts = [int(contract) for contract in self.exit_contracts.split(",")]

        # Calculate the total P&L
        total_entry_cost = sum(
            [price * contract for price, contract in zip(entry_prices, entry_contracts)]
        )
        total_exit_cost = sum(
            [price * contract for price, contract in zip(exit_prices, exit_contracts)]
        )
        pnl = round(total_exit_cost - total_entry_cost, 2)

        return pnl

    def total_entry_cost(self):
        entry_prices = [float(price) * 100 for price in self.entry_prices.split(",")]
        entry_contracts = [
            int(contract) for contract in self.entry_contracts.split(",")
        ]
        total_entry_cost = sum(
            [price * contract for price, contract in zip(entry_prices, entry_contracts)]
        )
        return round(total_entry_cost, 2)

    def total_exit_cost(self):
        exit_prices = [float(price) * 100 for price in self.exit_prices.split(",")]
        exit_contracts = [int(contract) for contract in self.exit_contracts.split(",")]
        total_exit_cost = sum(
            [price * contract for price, contract in zip(exit_prices, exit_contracts)]
        )
        return round(total_exit_cost, 2)

    def calculate_pnl_percent(self):
        pnl_percent = round(self.calculate_pnl() / self.total_entry_cost() * 100, 2)
        return pnl_percent

    def pnl(self):
        return f"${self.calculate_pnl()}"


def calculate_total_pnl():
    trades = Trade.query.all()
    total_pnl = sum([trade.calculate_pnl() for trade in trades])
    return round(total_pnl, 2)
