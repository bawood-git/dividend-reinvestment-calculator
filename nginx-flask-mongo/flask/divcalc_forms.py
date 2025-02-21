from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, TextAreaField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange    

class DivCalcForm(FlaskForm):
    csrf_token      = HiddenField()
    stock_symbol    = HiddenField()
    share_price     = HiddenField()
    initial_capital = DecimalField(default=1000.00, validators=[DataRequired(), NumberRange(min=0.01)])
    shares_owned    = DecimalField(default=0.00, validators=[DataRequired(), NumberRange(min=0.00)])
    distribution    = DecimalField(default=0.00)
    term            = IntegerField(default=12)
    frequency       = SelectField(choices=[
                                      ('Monthly', 'Monthly'),
                                      ('Quarterly', 'Quarterly'),
                                      ('Semiannual', 'Semiannual'),
                                      ('Annual', 'Annual')])
    contribution    = DecimalField(default=0.00)
    volatility      = DecimalField(default=0.00)
    purchase_mode   = SelectField( choices=[
                                      ('Fractional', 'Fractional'),
                                      ('Modulus', 'Modulus'),])
    run             = SubmitField()

class SettingsForm(FlaskForm):
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
