import json
import yfinance as yf
import config
import requests
import robin_stocks.robinhood as r
import time
from flask import (
    Blueprint,
    render_template,
    Response,
    redirect,
    url_for,
    flash,
    request,
    send_file,
    session,
    abort,
)
from sqlalchemy import desc, func
from app.models import *
import csv, sys, io
from .forms import OptionTradeForm, OrderForm, NewTradeForm
from datetime import datetime, date
import os
from jinja2 import Environment
from collections import defaultdict
from flask_login import current_user, login_user, login_required

trades_bp = Blueprint("trades_bp", __name__)


def check_for_session_portfolio(portfolio_id):
    # Check if the selected portfolio is different from the currently selected one
    if (
        "selected_portfolio_id" not in session
        or session["selected_portfolio_id"] != portfolio_id
    ):
        # Update the selected portfolio in the session
        session["selected_portfolio_id"] = portfolio_id
        # Perform any other necessary actions or updates


def return_portfolio_trades(portfolio_id, user):
    if portfolio_id:
        selected_portfolio = Portfolio.query.get(portfolio_id)
        if selected_portfolio.user != user:
            abort(
                403
            )  # Return a Forbidden HTTP response if the portfolio does not belong to the user
        trades = Trade.query.filter_by(portfolio_id=portfolio_id).order_by(
            desc(Trade.date_time)
        )
    else:
        selected_portfolio = user.portfolios[0]
        trades = Trade.query.filter_by(portfolio_id=selected_portfolio.id).order_by(
            desc(Trade.date_time)
        )
    return selected_portfolio, trades


def return_open_trades(portfolio_id):
    trades = Trade.query.filter(Trade.portfolio_id == portfolio_id).order_by(
        desc(Trade.date_time)
    )

    return trades


def convert_option_contract(ticker, option_contract):
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


@trades_bp.route("/dashboard", methods=["GET", "POST"])
@trades_bp.route("/dashboard/portfolio=<int:portfolio_id>", methods=["GET", "POST"])
@login_required
def dashboard(portfolio_id=None):
    check_for_session_portfolio(portfolio_id)
    user = User.query.filter_by(email=current_user.email).first()
    portfolios = user.portfolios
    if user.portfolios:
        selected_portfolio, trades = return_portfolio_trades(portfolio_id, user)
        trades = Trade.query.filter_by(portfolio_id=portfolio_id).order_by(
            desc(Trade.date_time)
        )
    else:
        flash("No portfolios exist, please create a portfolio", "warning")
        return redirect(url_for("default_bp.settings"))

    # Calculate trade count and P&L sum for each date
    trade_stats = defaultdict(lambda: {"trade_count": 0, "pnl_sum": 0, "trades": []})
    for trade in trades:  # Iterate over paginated trades
        if trade.status != "OPEN":
            trade_date = trade.close_date.date()
            trade_stats[trade_date]["trade_count"] += 1
            trade_stats[trade_date]["pnl_sum"] += trade.pnl
            trade_stats[trade_date]["trades"].append(trade.to_dict())

    # Prepare trade data for FullCalendar
    trade_data = []
    for trade_date, trade_stat in trade_stats.items():
        trade_data.append(
            {
                "title": f"{trade_stat['trade_count']} trade{'s' if trade_stat['trade_count'] > 1 else ''}",
                "start": trade_date.isoformat(),
                "color": "rgba(1,186,139, 0.7)"
                if trade_stat["pnl_sum"] >= 0
                else "rgba(210,72,57, 0.7)",
                "trade_count": trade_stat["trade_count"],
                "pnl_sum": trade_stat["pnl_sum"],
                "trades": trade_stat["trades"],
            }
        )
    pnl_data = selected_portfolio.calculate_cumulative_pnl()
    pnl_data = {str(date): pnl for date, pnl in pnl_data.items()}
    daily_pnl = selected_portfolio.calculate_daily_pnl()
    daily_pnl = {str(date): pnl for date, pnl in daily_pnl.items()}
    monthly_pnl = selected_portfolio.calculate_monthly_pnl()
    monthly_pnl = {str(date): pnl for date, pnl in monthly_pnl.items()}
    return render_template(
        "trades/dashboard.html",
        user=user,
        selected_portfolio=selected_portfolio,
        portfolios=portfolios,
        trades=trades,
        trade_data=trade_data,
        pnl_data=pnl_data,
        daily_pnl=daily_pnl,
        monthly_pnl=monthly_pnl,
    )


@trades_bp.route("/daily_journal")
@trades_bp.route("/daily_journal/portfolio=<int:portfolio_id>")
@login_required
def daily_journal(portfolio_id=None):
    check_for_session_portfolio(portfolio_id)
    user = User.query.filter_by(email=current_user.email).first()
    portfolios = user.portfolios
    if user.portfolios:
        selected_portfolio, trades = return_portfolio_trades(portfolio_id, user)
    else:
        flash("No portfolios exist, please create a portfolio", "warning")
        return redirect(url_for("default_bp.settings"))

    trade_journal = {}
    for trade in trades:
        if trade.status != "OPEN":
            trade_date = trade.close_date.date()

            # If the trade date is not already in the journal, create a new entry
            if trade_date not in trade_journal:
                trade_journal[trade_date] = {"trades": [], "pnl": 0}

            # Add the trade to the corresponding date entry in the journal
            trade_journal[trade_date]["trades"].append(trade)

            # Calculate and update the pnl for the day
            trade_journal[trade_date]["pnl"] += trade.pnl

    # Sort the trade journal by date
    sorted_journal = sorted(trade_journal.items(), key=lambda x: x[0], reverse=True)
    return render_template(
        "trades/daily_journal.html",
        journal=sorted_journal,
        selected_portfolio=selected_portfolio,
        portfolios=portfolios,
    )


@trades_bp.route("/trade_log", methods=["GET", "POST"])
@trades_bp.route("/trade_log/portfolio=<int:portfolio_id>")
@login_required
def trade_log(portfolio_id=None):
    check_for_session_portfolio(portfolio_id)
    user = User.query.filter_by(email=current_user.email).first()
    portfolios = user.portfolios
    if user.portfolios:
        selected_portfolio, trades = return_portfolio_trades(portfolio_id, user)
    else:
        flash("No portfolios exist, please create a portfolio", "warning")
        return redirect(url_for("default_bp.settings"))

    form = OptionTradeForm()
    return render_template(
        "trades/trade_log.html",
        trades=trades,
        selected_portfolio=selected_portfolio,
        portfolios=portfolios,
        form=form,
    )


@trades_bp.route("/open_trades", methods=["GET", "POST"])
@trades_bp.route("/open_trades/portfolio=<int:portfolio_id>", methods=["GET", "POST"])
@login_required
def open_trades(portfolio_id=None):
    check_for_session_portfolio(portfolio_id)
    user = User.query.filter_by(email=current_user.email).first()
    portfolios = user.portfolios
    if user.portfolios:
        selected_portfolio, trades = return_portfolio_trades(portfolio_id, user)
        trades = Trade.query.filter_by(portfolio_id=portfolio_id).order_by(
            desc(Trade.date_time)
        )
    else:
        flash("No portfolios exist, please create a portfolio", "warning")
        return redirect(url_for("default_bp.settings"))

    return render_template(
        "trades/open_trades.html",
        user=user,
        selected_portfolio=selected_portfolio,
        portfolios=portfolios,
        trades=trades,
    )


@trades_bp.route("/open_trades_mobile", methods=["GET", "POST"])
@trades_bp.route(
    "/open_trades_mobile/portfolio=<int:portfolio_id>", methods=["GET", "POST"]
)
@login_required
def open_trades_mobile(portfolio_id=None):
    check_for_session_portfolio(portfolio_id)
    user = User.query.filter_by(email=current_user.email).first()
    portfolios = user.portfolios
    if user.portfolios:
        selected_portfolio, trades = return_portfolio_trades(portfolio_id, user)
        trades = Trade.query.filter_by(portfolio_id=portfolio_id).order_by(
            desc(Trade.date_time)
        )
    else:
        flash("No portfolios exist, please create a portfolio", "warning")
        return redirect(url_for("default_bp.settings"))

    return render_template(
        "trades/open_trades_mobile.html",
        user=user,
        selected_portfolio=selected_portfolio,
        portfolios=portfolios,
        trades=trades,
    )


@trades_bp.route("/trades", methods=["GET", "POST"])
@trades_bp.route("/trades/portfolio=<int:portfolio_id>", methods=["GET", "POST"])
@login_required
def list_trades(portfolio_id=None):
    portfolios = Portfolio.query.all()

    if not portfolios:
        flash("No portfolio found, please create one", "warning")
        return redirect(url_for("default_bp.settings"))

    if portfolio_id:
        selected_portfolio = Portfolio.query.get(portfolio_id)
        trades = Trade.query.filter_by(portfolio_id=portfolio_id).order_by(
            desc(Trade.date_time)
        )
    else:
        selected_portfolio = Portfolio.query.first()
        trades = Trade.query.filter_by(portfolio_id=selected_portfolio.id).order_by(
            desc(Trade.date_time)
        )

    # Calculate trade count and P&L sum for each date
    trade_stats = defaultdict(lambda: {"trade_count": 0, "pnl_sum": 0})
    for trade in trades:  # Iterate over paginated trades
        trade_date = trade.date_time.date()
        trade_stats[trade_date]["trade_count"] += 1
        trade_stats[trade_date]["pnl_sum"] += trade.pnl

    # Prepare trade data for FullCalendar
    trade_data = []
    for trade_date, trade_stat in trade_stats.items():
        trade_data.append(
            {
                "title": f"{trade_stat['trade_count']} trades",
                "start": trade_date.isoformat(),
                "color": "green" if trade_stat["pnl_sum"] >= 0 else "red",
                "trade_count": trade_stat["trade_count"],
                "pnl_sum": trade_stat["pnl_sum"],
            }
        )

    form = OptionTradeForm()

    return render_template(
        "trades/list_trades.html",
        portfolios=portfolios,
        trades=trades,
        selected_portfolio=selected_portfolio,
        form=form,
        trade_data=trade_data,
    )


@trades_bp.route("/edit_trade/<int:trade_id>", methods=["POST"])
@login_required
def edit_trade(trade_id):
    trade = Trade.query.get(trade_id)
    if trade:
        # Get the selected setup and mistake IDs from the form
        selected_setups = request.form.getlist("setups")
        selected_mistakes = request.form.getlist("mistakes")

        # Clear existing setups and mistakes associated with the trade
        trade.setups.clear()
        trade.mistakes.clear()

        # Add the selected setups and mistakes to the trade
        for setup_id in selected_setups:
            setup = Setup.query.get(setup_id)
            if setup:
                trade.setups.append(setup)

        for mistake_id in selected_mistakes:
            mistake = Mistake.query.get(mistake_id)
            if mistake:
                trade.mistakes.append(mistake)

        # Commit the changes to the database
        db.session.commit()
        flash("Tags updated successfully!", "success")
    else:
        flash("Invalid trade ID. Please try again.", "danger")
    return redirect(request.referrer)


@trades_bp.route("/edit_current_price/<int:trade_id>", methods=["POST"])
@login_required
def edit_current_price(trade_id):
    trade = Trade.query.get(trade_id)
    if trade:
        current_price = request.form.get("current_price")
        trade.current_price = current_price
        db.session.commit()
        flash("Current price set", "success")
    else:
        flash("Invalid trade ID. Please try again.", "danger")
    return redirect(request.referrer)


@trades_bp.route("/get_current_price/<int:trade_id>")
@login_required
def get_current_price(trade_id):
    trade = Trade.query.get(trade_id)
    if trade:
        if trade.market == "Options":
            parts = trade.instrument.split(" ")
            option_type = parts[2].lower()
            date_str = trade.instrument.split()[0]
            date_obj = datetime.strptime(date_str, "%m-%d-%Y").date()
            converted_date_str = date_obj.strftime("%Y-%m-%d")

            # contract = convert_option_contract(trade.symbol, trade.instrument)

            r.login()
            option = r.options.get_option_market_data(
                inputSymbols=trade.symbol,
                expirationDate=converted_date_str,
                strikePrice=parts[1],
                optionType=option_type,
            )
            if option:
                last_price = round(float(option[0][0]["adjusted_mark_price"]), 2)
            else:
                last_price = 0
            r.logout()

            # yfsymbol = yf.Ticker(trade.symbol)
            # opt = yfsymbol.option_chain(date=converted_date_str)

            # if option_type == "CALL":
            #     last_price = opt.calls.loc[
            #         opt.calls.contractSymbol == contract, "lastPrice"
            #     ].values[-1]
            # elif option_type == "PUT":
            #     last_price = opt.puts.loc[
            #         opt.puts.contractSymbol == contract, "lastPrice"
            #     ].values[-1]

            trade.current_price = last_price
            db.session.commit()
            flash("Current price set", "success")
        if trade.market == "Stock":
            r.login()
            stock = r.stocks.get_latest_price(trade.symbol)
            if stock:
                last_price = stock[0]
            else:
                last_price = 0
            r.logout()
            trade.current_price = last_price
            db.session.commit()
            flash("Current price set", "success")
    return redirect(request.referrer)


@trades_bp.route("/get_current_price_new/<int:trade_id>")
@login_required
def get_current_price_new(trade_id):
    trade = Trade.query.get(trade_id)
    if trade:
        url = f"{config.API_BASE_URL}markets/quotes"
        headers = {
            "Authorization": f"Bearer {config.API_ACCESS_TOKEN}",
            "Accept": "application/json",
        }
        if trade.market == "Options":
            parts = trade.instrument.split(" ")
            option_type = parts[2].lower()
            date_str = trade.instrument.split()[0]
            date_obj = datetime.strptime(date_str, "%m-%d-%Y").date()
            converted_date_str = date_obj.strftime("%Y-%m-%d")

            contract = convert_option_contract(trade.symbol, trade.instrument)

            response = requests.get(url, params={"symbols": contract}, headers=headers)
            json_response = response.json()
            bid = json_response["quotes"]["quote"]["bid"]
            ask = json_response["quotes"]["quote"]["ask"]
            spread = ask - bid
            mid_price = round(ask - (spread / 2), 2)

            trade.current_price = mid_price
            db.session.commit()
            flash("Current price set", "success")
        if trade.market == "Stock":
            response = requests.get(
                url, params={"symbols": trade.symbol}, headers=headers
            )

            json_response = response.json()
            bid = json_response["quotes"]["quote"]["bid"]
            ask = json_response["quotes"]["quote"]["ask"]
            spread = ask - bid
            mid_price = round(ask - (spread / 2), 2)

            trade.current_price = mid_price
            db.session.commit()
            flash("Current price set", "success")
    return redirect(request.referrer)


@trades_bp.route("/get_current_price_open_trades/portfolio=<int:portfolio_id>")
@login_required
def get_current_price_open_trades(portfolio_id):
    check_for_session_portfolio(portfolio_id)
    user = User.query.filter_by(email=current_user.email).first()
    trades = Trade.query.filter_by(portfolio_id=portfolio_id).order_by(
        desc(Trade.date_time)
    )
    trades = [trade for trade in trades if trade.status == "OPEN"]
    r.login()
    for trade in trades:
        if trade.market == "Options":
            parts = trade.instrument.split(" ")
            option_type = parts[2].lower()
            date_str = trade.instrument.split()[0]
            date_obj = datetime.strptime(date_str, "%m-%d-%Y").date()
            converted_date_str = date_obj.strftime("%Y-%m-%d")

            option = r.options.get_option_market_data(
                inputSymbols=trade.symbol,
                expirationDate=converted_date_str,
                strikePrice=parts[1],
                optionType=option_type,
            )
            last_price = round(float(option[0][0]["adjusted_mark_price"]), 2)
            trade.current_price = last_price
            db.session.commit()
            time.sleep(0.25)
    flash("Current price set", "success")
    r.logout()
    return redirect(request.referrer)


@trades_bp.route("/get_current_price_open_trades_new/portfolio=<int:portfolio_id>")
@login_required
def get_current_price_open_trades_new(portfolio_id):
    check_for_session_portfolio(portfolio_id)
    user = User.query.filter_by(email=current_user.email).first()
    trades = Trade.query.filter_by(portfolio_id=portfolio_id).order_by(
        desc(Trade.date_time)
    )
    trades = [trade for trade in trades if trade.status == "OPEN"]

    symbols = []
    for trade in trades:
        if trade.market == "Options":
            contract = convert_option_contract(trade.symbol, trade.instrument)
            symbols.append(contract)
        elif trade.market == "Stock":
            symbols.append(trade.symbol)

    symbols_str = ",".join(symbols)
    print(symbols_str)
    url = f"{config.API_BASE_URL}markets/quotes"
    headers = {
        "Authorization": f"Bearer {config.API_ACCESS_TOKEN}",
        "Accept": "application/json",
    }

    response = requests.get(url, params={"symbols": symbols_str}, headers=headers)
    json_response = response.json()
    quotes = json_response.get("quotes", {}).get("quote", [])
    print(quotes)
    for trade in trades:
        for quote in quotes:
            if trade.api_symbol == quote["symbol"]:
                bid = quote["bid"]
                ask = quote["ask"]
                spread = ask - bid
                mid_price = round(ask - (spread / 2), 2)
                print(trade.symbol, mid_price)

                trade.current_price = mid_price
                db.session.commit()
                break

    flash("Current price set", "success")
    return redirect(request.referrer)


@trades_bp.route("/delete_trade/<int:trade_id>", methods=["POST"])
@login_required
def delete_trade(trade_id):
    trade = Trade.query.get(trade_id)
    if trade:
        db.session.delete(trade)
        db.session.commit()
    return redirect(request.referrer)


@trades_bp.route("/trades/<int:trade_id>", methods=["GET"])
@login_required
def trade_details(trade_id):
    trade = Trade.query.filter_by(id=trade_id).first_or_404()
    user = User.query.filter_by(email=current_user.email).first()
    if trade.portfolio.user != user:
        abort(403)
    form = OrderForm()
    return render_template(
        "trades/trade_details.html", trade=trade, form=form, user=user
    )


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_image_file(filename):
    """
    Check if the provided filename has an allowed image extension.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_image_file_path(portfolio_id, trade_id, filename):
    """
    Generate the file path for storing the image file.
    """
    base_path = f"{os.getcwd()}/app/static/img/"
    portfolio_path = os.path.join(
        base_path, "trade-img", "portfolio", str(portfolio_id)
    )
    trade_path = os.path.join(portfolio_path, "trade", str(trade_id))
    file_path = os.path.join(trade_path, filename)

    # Create the directories if they don't exist
    os.makedirs(trade_path, exist_ok=True)

    return file_path


@trades_bp.route("/trades/<int:trade_id>/upload_image", methods=["GET", "POST"])
@login_required
def upload_image(trade_id):
    trade = Trade.query.filter_by(id=trade_id).first_or_404()
    if request.method == "POST":
        # Check if the request contains a file
        if "image" not in request.files:
            flash("No file part", "danger")
            return redirect(url_for("trades_bp.trade_details", trade_id=trade_id))

        image_file = request.files["image"]

        # Check if the file exists and has an allowed extension
        if image_file and allowed_image_file(image_file.filename):
            image_file.filename = (
                f"trade-{trade_id}-{abs(hash(image_file.filename))}.png"
            )
            # Generate the file path
            file_path = get_image_file_path(
                trade.portfolio_id, trade.id, image_file.filename
            )
            # Save the file to the specified path
            image_file.save(file_path)
            object_filename = file_path.replace(f"{os.getcwd()}/app", "")
            img = Image(filename=object_filename, trade_id=trade_id)
            db.session.add(img)
            db.session.commit()

            flash("Image uploaded successfully", "success")
            return redirect(url_for("trades_bp.trade_details", trade_id=trade_id))

        flash("Invalid file type or missing image", "danger")
        return redirect(url_for("trades_bp.trade_details", trade_id=trade_id))


@trades_bp.route("/trades/delete_image/<int:image_id>", methods=["POST"])
@login_required
def delete_image(image_id):
    image = Image.query.get_or_404(image_id)
    if image:
        db.session.delete(image)
        db.session.commit()

    # Redirect to the trade details page
    return redirect(request.referrer)


@trades_bp.route("/new_trade", methods=["GET", "POST"])
@login_required
def new_trade():
    form = NewTradeForm()
    if form.validate_on_submit():
        if form.market.data == "Options":
            instrument = f"{form.expiration_date.data.strftime('%m-%d-%Y')} {int(form.strike_price.data)} {form.call_put.data.upper()}"
        else:
            instrument = form.market.data
        trade = Trade(
            symbol=form.symbol.data,
            market=form.market.data,
            instrument=instrument,
            date_time=form.date_time.data,
            portfolio_id=form.portfolio.data,
        )
        db.session.add(trade)
        db.session.commit()

        if form.action.data == "sell":
            quantity = -form.quantity.data
        else:
            quantity = form.quantity.data

        # Create the first order for the trade
        order = Order(
            date_time=form.date_time.data,
            price=form.price.data,
            quantity=quantity,
            trade=trade,
        )
        db.session.add(order)
        db.session.commit()
        return redirect(url_for("trades_bp.trade_details", trade_id=trade.id))

    return render_template("trades/add_trade.html", form=form)


@trades_bp.route("/add_trade", methods=["GET", "POST"])
@login_required
def add_trade():
    form = OptionTradeForm()
    if form.validate_on_submit():
        # Create a new trade based on the form data
        if form.market.data == "Options":
            instrument = f"{form.expiration_date.data.strftime('%m-%d-%Y')} {int(form.strike_price.data)} {form.call_put.data.upper()}"
        else:
            instrument = form.market.data
        trade = Trade(
            symbol=form.symbol.data,
            market=form.market.data,
            instrument=instrument,
            date_time=form.date_time.data,
            portfolio_id=form.portfolio.data,
        )
        db.session.add(trade)
        db.session.commit()

        if form.action.data == "sell":
            quantity = -form.quantity.data
        else:
            quantity = form.quantity.data

        # Create the first order for the trade
        order = Order(
            date_time=form.date_time.data,
            price=form.price.data,
            quantity=quantity,
            trade=trade,
        )
        db.session.add(order)
        db.session.commit()

        return redirect(url_for("trades_bp.trade_details", trade_id=trade.id))


@trades_bp.route("/trade/<int:trade_id>/add_order", methods=["GET", "POST"])
@login_required
def add_order(trade_id):
    trade = Trade.query.get(trade_id)
    form = OrderForm()
    if form.validate_on_submit():
        if form.action.data == "Sell":
            quantity = -form.quantity.data
        else:
            quantity = form.quantity.data
        # Create a new order based on the form data
        order = Order(
            date_time=form.date_time.data,
            price=form.price.data,
            quantity=quantity,
            trade=trade,
        )
        db.session.add(order)
        db.session.commit()
        return redirect(url_for("trades_bp.trade_details", trade_id=trade.id))
    return redirect(url_for("trades_bp.trade_details", trade_id=trade.id))


@trades_bp.route("/orders/<order_id>", methods=["POST"])
@login_required
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    form = OrderForm()
    if form.action.data == "Sell":
        quantity = -form.quantity.data
    else:
        quantity = form.quantity.data
    if form.validate_on_submit():
        order.date_time = form.date_time.data
        order.action = form.action.data
        order.price = form.price.data
        order.quantity = quantity

        db.session.commit()
        flash("Order updated successfully!", "success")

    return redirect(url_for("trades_bp.trade_details", trade_id=order.trade.id))


@trades_bp.route("/trades/<int:trade_id>/update_trade_notes", methods=["POST"])
@login_required
def update_trade_notes(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    trade.trade_notes = request.form.get("trade_notes")
    db.session.commit()
    # flash("Trade notes updated successfully.", "success")
    return redirect(url_for("trades_bp.trade_details", trade_id=trade_id))


@trades_bp.route(
    "/trade_details/delete_order/<int:order_id>", methods=["POST", "DELETE"]
)
@login_required
def delete_order(order_id):
    # Get the order from the database based on the order_id
    order = Order.query.get_or_404(order_id)

    # Check if it is the last order in the trade
    trade = order.trade
    if len(trade.orders) == 1:
        flash("You cannot delete the last order of the trade.", "error")
        return redirect(url_for("trades_bp.trade_details", trade_id=trade.id))

    # Delete the order from the database
    db.session.delete(order)
    db.session.commit()

    # Redirect the user back to the trade_details page
    return redirect(url_for("trades_bp.trade_details", trade_id=trade.id))


@trades_bp.route("/trades/export-csv")
@trades_bp.route("/trades/portfolio=<int:portfolio_id>/export-csv")
@login_required
def export_trades_csv(portfolio_id=None):
    if portfolio_id:
        trades = (
            Trade.query.filter_by(portfolio_id=portfolio_id)
            .order_by(desc(Trade.date_time))
            .all()
        )
    else:
        trades = Trade.query.all()
    # Create the CSV data
    csv_data = io.StringIO()
    csv_writer = csv.writer(csv_data)
    csv_writer.writerow(
        [
            "Trade ID",
            "Symbol",
            "Market",
            "Instrument",
            "Order Date/Time",
            "Price",
            "Quantity",
        ]
    )

    for trade in trades:
        for order in trade.orders:
            csv_writer.writerow(
                [
                    trade.id,
                    trade.symbol,
                    trade.market,
                    trade.instrument,
                    order.date_time.strftime("%Y-%m-%d %H:%M:%S"),
                    order.price,
                    order.quantity,
                ]
            )

    # Prepare the CSV file for download
    csv_data.seek(0)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=trades.csv"},
    )


def import_csv(file_path, portfolio_id):
    trades = {}

    with open(file_path, "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header row

        for row in csv_reader:
            trade_id = int(row[0])
            symbol = row[1]
            market = row[2]
            instrument = row[3]
            date_time = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
            price = float(row[5])
            quantity = int(row[6])

            existing_order = (
                Order.query.join(Trade)
                .filter(
                    Trade.symbol == symbol,
                    Trade.instrument == instrument,
                    Trade.portfolio_id == portfolio_id,
                    func.strftime("%Y-%m-%d %H:%M:%S", Trade.date_time)
                    == date_time.strftime("%Y-%m-%d %H:%M:%S"),
                    func.strftime("%Y-%m-%d %H:%M:%S", Order.date_time)
                    == date_time.strftime("%Y-%m-%d %H:%M:%S"),
                    Order.price == price,
                    Order.quantity == quantity,
                )
                .first()
            )

            if existing_order:
                continue  # Skip importing if order already exists

            if trade_id not in trades:
                # Create a new trade if it doesn't exist
                new_trade = Trade(
                    symbol=symbol,
                    market=market,
                    instrument=instrument,
                    date_time=date_time,
                    portfolio_id=portfolio_id,
                )
                trades[trade_id] = new_trade
                db.session.add(new_trade)
            else:
                # Use the existing trade
                new_trade = trades[trade_id]

            new_order = Order(
                date_time=date_time,
                price=price,
                quantity=quantity,
                trade=new_trade,
            )
            db.session.add(new_order)

    db.session.commit()


@trades_bp.route("/trades/portfolio=<int:portfolio_id>/import_csv", methods=["POST"])
@login_required
def import_csv_route(portfolio_id):
    csv_file = request.files["csvFile"]
    if csv_file:
        file_path = csv_file.filename
        csv_file.save(file_path)
        import_csv(file_path, portfolio_id)
        return redirect(url_for("trades_bp.list_trades", portfolio_id=portfolio_id))
    else:
        return "No CSV file provided."
