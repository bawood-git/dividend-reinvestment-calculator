from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, TextAreaField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange    

class DivCalcForm(FlaskForm):
    source          = HiddenField()
    csrf_token      = HiddenField()
    stock_symbol    = HiddenField()
    initial_capital = DecimalField(default=1000.00)
    share_price     = DecimalField(default=10.00,   validators=[DataRequired(), NumberRange(min=0.01)])
    shares_owned    = DecimalField(default=0.00,    validators=[DataRequired(), NumberRange(min=0.00)])
    distribution    = DecimalField(default=0.10,    validators=[DataRequired(), NumberRange(min=0.00)])
    term            = IntegerField(default=12,      validators=[DataRequired(), NumberRange(min=1)])
    contribution    = DecimalField(default=0.00)
    volatility      = DecimalField(default=0.00,    validators=[DataRequired(), NumberRange(min=0.00)])
    frequency       = SelectField(choices=[
                                      ('Monthly', 'Monthly'),
                                      ('Quarterly', 'Quarterly'),
                                      ('Semiannual', 'Semiannual'),
                                      ('Annual', 'Annual')])
    purchase_mode   = SelectField( choices=[
                                      ('Fractional', 'Fractional'),
                                      ('Modulus', 'Modulus'),])
    run             = SubmitField()

class StockSettingsForm(FlaskForm):
    source          = HiddenField(default='stock_settings')
    initial_capital = DecimalField(default=1000.00, validators=[DataRequired(), NumberRange(min=0.01)])
    shares_owned    = DecimalField(default=0.00)
    term            = IntegerField(default=12)
    frequency       = SelectField(choices=[
                                      ('Monthly', 'Monthly'),
                                      ('Quarterly', 'Quarterly'),
                                      ('Semiannual', 'Semiannual'),
                                      ('Annual', 'Annual')])
    contribution    = DecimalField(default=0.00)
    purchase_mode   = SelectField( choices=[
                                      ('Fractional', 'Fractional'),
                                      ('Modulus', 'Modulus'),])
    save            = SubmitField()

class APISettingsForm(FlaskForm):
    source          = HiddenField(default='api_settings')
    api_tst         = HiddenField()
    api_key         = StringField()
    api_src         = SelectField(choices=[
                                      ('Manual', 'Manual'),
                                      ('AlphaVantage', 'AlphaVantage'),])
    test            = SubmitField()

class LoginForm(FlaskForm):
    source          = HiddenField(default='login')
    username        = StringField()
    login           = SubmitField()
