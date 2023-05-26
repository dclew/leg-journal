from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
    jsonify,
)
from .models import Portfolio
from .forms import PortfolioForm
from app import db
from flask_login import current_user, login_user, login_required
from app.models import User

default_bp = Blueprint("default_bp", __name__, url_prefix="/")


@default_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("default_bp.settings"))
    else:
        flash("Please login to access settings")
        return redirect(url_for("auth_bp.login"))


@default_bp.route("/set_selected_portfolio", methods=["POST"])
@login_required
def set_selected_portfolio():
    portfolio_id = request.json.get("portfolioId")
    session["selected_portfolio_id"] = portfolio_id
    return jsonify({"message": "Selected portfolio updated successfully."})


@default_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = User.query.filter_by(email=current_user.email).first()
    form = PortfolioForm()

    if request.method == "POST" and form.validate_on_submit():
        portfolio_name = form.name.data

        # Create a new portfolio
        new_portfolio = Portfolio(name=portfolio_name, user_id=current_user.id)
        db.session.add(new_portfolio)
        db.session.commit()
        session["selected_portfolio_id"] = new_portfolio.id

        return redirect(
            url_for("default_bp.settings")
        )  # Redirect back to the settings page after creating a portfolio

    portfolios = user.portfolios

    return render_template("settings.html", form=form, portfolios=portfolios, user=user)


@default_bp.route("/edit_portfolio_name/<int:portfolio_id>", methods=["POST"])
@login_required
def edit_portfolio_name(portfolio_id):
    form = PortfolioForm()
    portfolio = Portfolio.query.get(portfolio_id)
    if form.validate_on_submit():
        new_portfolio_name = form.name.data
        portfolio.name = new_portfolio_name
        db.session.commit()
        flash("Portfolio updated successfully!")
    else:
        flash("Invalid form submission. Please try again.")

    return redirect(url_for("default_bp.settings"))


@default_bp.route("/set_default_portfolio", methods=["POST"])
@login_required
def set_default_portfolio():
    user = User.query.filter_by(email=current_user.email).first()
    default_portfolio_id = request.form.get("default_portfolio")

    # Update the default_portfolio_id field for the user
    user.default_portfolio_id = default_portfolio_id
    db.session.commit()

    flash("Default portfolio updated successfully.")
    return redirect(url_for("default_bp.settings"))
