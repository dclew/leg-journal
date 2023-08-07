from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError


class PortfolioForm(FlaskForm):
    name = StringField("Portfolio Name", validators=[DataRequired()])
