from flask import (
    Blueprint,
    render_template,
    Response,
    redirect,
    url_for,
    flash,
    request,
)
from app.models import Trade, db
import csv
from io import StringIO
from .forms import TradeForm

trades_bp = Blueprint("trades_bp", __name__)


@trades_bp.route("/trades", methods=["GET", "POST"])
def list_trades():
    trades = Trade.query.order_by(Trade.open_date.desc()).all()
    return render_template(
        "trades/list_trades.html",
        trades=trades,
    )


@trades_bp.route("/delete_trade/<int:trade_id>", methods=["POST"])
def delete_trade(trade_id):
    trade = Trade.query.get(trade_id)
    if trade:
        db.session.delete(trade)
        db.session.commit()
    return redirect(url_for("trades_bp.list_trades"))


@trades_bp.route("/trades/<int:trade_id>", methods=["GET"])
def trade_details(trade_id):
    trade = Trade.query.filter_by(id=trade_id).first_or_404()
    return render_template("trades/trade_details.html", trade=trade)


# @trades_bp.route("/trades/export-csv")
# def export_trades_csv():
#     trades = Trade.query.all()
#     output = StringIO()
#     writer = csv.writer(output)
#     writer.writerow(
#         [
#             "Symbol",
#             "Trade Date",
#             "Entry Times",
#             "Entry Prices",
#             "Entry Contracts",
#             "Exit Times",
#             "Exit Prices",
#             "Exit Contracts",
#         ]
#     )
#     for trade in trades:
#         writer.writerow(
#             [
#                 trade.symbol,
#                 trade.trade_date,
#                 trade.entry_times,
#                 trade.entry_prices,
#                 trade.entry_contracts,
#                 trade.exit_times,
#                 trade.exit_prices,
#                 trade.exit_contracts,
#             ]
#         )
#     output.seek(0)
#     return Response(
#         output,
#         mimetype="text/csv",
#         headers={"Content-Disposition": "attachment; filename=trades.csv"},
#     )
