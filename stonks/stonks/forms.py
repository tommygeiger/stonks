from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, RadioField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, NumberRange
from wtforms import ValidationError


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')


class TradeForm(FlaskForm):
    symbol = StringField('Symbol', validators=[DataRequired(), Length(1, 5)])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    buy = SubmitField('Buy')
    sell = SubmitField('Sell')

class ResearchForm(FlaskForm):
    symbol = StringField('Symbol', validators=[DataRequired(), Length(1, 5)])
    #timeframe = RadioField('Timeframe', choices=[('5d', 'Last 5 Days'), ('1mo', 'Last Month'), ('3mo', 'Last 3 Months'), ('6mo', 'Last 6 months'), ('1y', 'Last Year'), ('2y', 'Last 2 Years'), ('5y', 'Last 5 Years'), ('10y', 'Last 10 Years'), ('ytd', 'Current Calandar Year'), ('max', 'Maximum')])
    search = SubmitField('Search')
