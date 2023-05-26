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
)
from flask_login import current_user, login_user, logout_user
from app.auth.forms import (
    LoginForm,
    RegistrationForm,
    ResetPasswordRequestForm,
    ResetPasswordForm,
)
from app.models import User
from app import db

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("default_bp.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("auth_bp.login"))
        login_user(user, remember=form.remember_me.data)
        flash("Welcome {}".format(user.email))
        return redirect(url_for("default_bp.index"))
    return render_template("auth/login.html", title="Sign In", form=form)


@auth_bp.route("/logout")
def logout():
    session.clear()
    logout_user()
    return redirect(url_for("default_bp.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("default_bp.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("auth_bp.login"))
    return render_template("auth/register.html", title="Register", form=form)


# @auth_bp.route("/reset_password_request", methods=["GET", "POST"])
# def reset_password_request():
#     if current_user.is_authenticated:
#         return redirect(url_for("main.index"))
#     form = ResetPasswordRequestForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user:
#             send_password_reset_email(user)
#         flash("Check your email for the instructions to reset your password")
#         return redirect(url_for("auth.login"))
#     return render_template(
#         "auth/reset_password_request.html", title="Reset Password", form=form
#     )


# @auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
# def reset_password(token):
#     if current_user.is_authenticated:
#         return redirect(url_for("main.index"))
#     user = User.verify_reset_password_token(token)
#     if not user:
#         return redirect(url_for("main.index"))
#     form = ResetPasswordForm()
#     if form.validate_on_submit():
#         user.set_password(form.password.data)
#         db.session.commit()
#         flash("Your password has been reset.")
#         return redirect(url_for("auth.login"))
#     return render_template("auth/reset_password.html", form=form, user=user)
