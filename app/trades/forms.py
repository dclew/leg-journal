from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField
from wtforms.validators import DataRequired


class TradeForm(FlaskForm):
    symbol = StringField("Symbol", validators=[DataRequired()])
    trade_date = DateField("Trade Date", validators=[DataRequired()])
    entry_prices = StringField("Entry Prices", validators=[DataRequired()])
    entry_contracts = StringField("Entry Contracts", validators=[DataRequired()])
    exit_prices = StringField("Exit Price", validators=[DataRequired()])
    exit_contracts = StringField("Exit Contracts", validators=[DataRequired()])
