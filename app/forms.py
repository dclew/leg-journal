from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class PortfolioForm(FlaskForm):
    name = StringField("Portfolio Name", validators=[DataRequired()])
