from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    DecimalField,
    DateField,
    IntegerField,
    FloatField,
    DateTimeField,
    SubmitField,
    DateTimeLocalField,
    SelectField,
)
from wtforms.validators import DataRequired, Optional, ValidationError
from flask_login import current_user
from app.models import User


class OptionTradeForm(FlaskForm):
    market = SelectField(
        "Market",
        choices=[("Stock", "Stock"), ("Options", "Options"), ("Crypto", "Crypto")],
        validators=[DataRequired()],
    )
    symbol = StringField("Symbol", validators=[DataRequired()])
    date_time = DateTimeLocalField(
        "Open Date", format="%Y-%m-%d %H:%M", validators=[DataRequired()]
    )
    action = SelectField(
        "Action",
        choices=[("buy", "Buy"), ("sell", "Sell")],
        validators=[DataRequired()],
    )
    call_put = SelectField(
        "Call/Put",
        choices=[("call", "Call"), ("put", "Put")],
        validators=[DataRequired()],
    )
    expiration_date = DateField("Expiration Date", validators=[Optional()])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
    price = FloatField("Price", validators=[DataRequired()])
    strike_price = FloatField("Strike Price", validators=[Optional()])
    portfolio = StringField("Portfolio", validators=[DataRequired()])

    def validate(self):
        if not super().validate():
            return False

        if self.market.data == "Options":
            if not self.call_put.data:
                self.call_put.errors.append(
                    "Call/Put selection is required for Options trades."
                )
                return False
            if not self.expiration_date.data:
                self.expiration_date.errors.append(
                    "Expiration date is required for Options trades."
                )
                return False
            if not self.strike_price.data:
                self.strike_price.errors.append(
                    "Strike price is required for Options trades."
                )
                return False

        return True

    def validate_on_submit(self):
        if not self.is_submitted():
            return False

        for field in self:
            if isinstance(field.data, str) and not field.data.strip():
                raise ValidationError(f"{field.label.text} is required.")

        return self.validate()


class NewTradeForm(FlaskForm):
    portfolio = SelectField("Portfolio", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.portfolio.choices = [
            (portfolio.id, portfolio.name) for portfolio in current_user.portfolios
        ]

    market = SelectField(
        "Market",
        choices=[("Stock", "Stock"), ("Options", "Options"), ("Crypto", "Crypto")],
        validators=[DataRequired()],
    )
    symbol = StringField("Symbol", validators=[DataRequired()])
    date_time = DateTimeLocalField(
        "Open Date", format="%Y-%m-%d %H:%M", validators=[DataRequired()]
    )
    action = SelectField(
        "Action",
        choices=[("buy", "Buy"), ("sell", "Sell")],
        validators=[DataRequired()],
    )
    call_put = SelectField(
        "Call/Put",
        choices=[("call", "Call"), ("put", "Put")],
        validators=[DataRequired()],
    )
    expiration_date = DateField("Expiration Date", validators=[Optional()])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
    price = FloatField("Price", validators=[DataRequired()])
    strike_price = FloatField("Strike Price", validators=[Optional()])

    def validate(self):
        if not super().validate():
            return False

        if self.market.data == "Options":
            if not self.call_put.data:
                self.call_put.errors.append(
                    "Call/Put selection is required for Options trades."
                )
                return False
            if not self.expiration_date.data:
                self.expiration_date.errors.append(
                    "Expiration date is required for Options trades."
                )
                return False
            if not self.strike_price.data:
                self.strike_price.errors.append(
                    "Strike price is required for Options trades."
                )
                return False

        return True

    def validate_on_submit(self):
        if not self.is_submitted():
            return False

        for field in self:
            if isinstance(field.data, str) and not field.data.strip():
                raise ValidationError(f"{field.label.text} is required.")

        return self.validate()


class OrderForm(FlaskForm):
    date_time = DateTimeLocalField(
        "Date/Time", format="%Y-%m-%d %H:%M", validators=[DataRequired()]
    )
    action = SelectField(
        "Action",
        choices=[("Buy", "Buy"), ("Sell", "Sell")],
        validators=[DataRequired()],
    )
    price = FloatField("Price", validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
