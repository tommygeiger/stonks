import os
import requests
import yfinance as yf
from flask import Flask, flash, jsonify, render_template, request , session, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import ValidationError
from forms import LoginForm, RegistrationForm, TradeForm, ResearchForm
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime, timedelta
from io import BytesIO
from decimal import *
import re



#Init
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'hard to guess string'
bootstrap = Bootstrap(app)
application = app


#Connect to db
mysql = MySQL()
mysql.init_app(app)
app.config['MYSQL_DATABASE_USER'] = 'tgeigerd'
app.config['MYSQL_DATABASE_PASSWORD'] = '2tX6jF19[Q)jTf'
app.config['MYSQL_DATABASE_DB'] = 'tgeigerd_Stonks'
db = mysql.connect()
cursor = db.cursor()



@app.route('/')
def index():
	return redirect(url_for('login'))


@app.route('/login', methods=['GET','POST'])
def login():

	if 'loggedin' in session:
		return redirect(url_for('portfolio'))

	else:
		form = LoginForm()
		if form.validate_on_submit():
			username = form.username.data.lower()
			password = form.password.data
			cursor.execute("SELECT * FROM Users WHERE username=%s", username)
			user = cursor.fetchone()
			if user and check_password_hash(user[3], password):
				session['loggedin'] = True
				session['id'] = user[0]
				session['username'] = user[2]
				return redirect(url_for('portfolio'))
			flash('Invalid username or password')
		return render_template('login.html', form=form)




@app.route('/register', methods=['GET','POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		email = form.email.data.lower()
		username = form.username.data.lower()
		password = generate_password_hash(form.password.data)
		cursor.execute("SELECT * FROM Users WHERE email=%s", email)
		if cursor.fetchone():
			flash('Email already registered.')
			return render_template('register.html', form=form)
		cursor.execute("SELECT * FROM Users WHERE username=%s", username)
		if cursor.fetchone():
			flash('Username already in use.')
			return render_template('register.html', form=form)
		cursor.execute("INSERT IGNORE INTO Users VALUES (NULL, %s, %s, %s, 1000.00, %s)", (email, username, password, datetime.now().date()))
		db.commit()
		return redirect(url_for('login'))
	return render_template('register.html', form=form)


@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('username', None)
	flash('You have been logged out.')
	return redirect(url_for('login'))


@app.route('/trade', methods=['GET','POST'])
def trade():

	if 'loggedin' not in session:
		flash('Log In or Sign Up to start trading!')
		return redirect(url_for('login'))

	form = TradeForm()
	if form.validate_on_submit():

		#Get stock
		symbol = form.symbol.data.upper()
		quantity = form.quantity.data
		try:
			stock = yf.Ticker(symbol)
			ask = stock.info['ask']
			trade_amount = ask*quantity

			if form.buy.data:
				#Get cash
				cursor.execute("SELECT * FROM Users WHERE id=%s", session['id'])
				for row in cursor:
					cash = row[4]

				if trade_amount <= cash:
					#Subtract ask from cash, insert stock
					cursor.execute("UPDATE Users SET cash=cash-%s WHERE id=%s", (trade_amount, session['id']))

					#Increment quantity if owned, otherwise add
					cursor.execute("SELECT * FROM Stocks WHERE id=%s AND symbol=%s", (session['id'], symbol))
					if cursor.fetchone():
						cursor.execute("UPDATE Stocks SET quantity=quantity+%s, date=%s WHERE id=%s", (quantity, datetime.now().date(), session['id']))
					else:
						cursor.execute("INSERT INTO Stocks VALUES (%s, %s, %s, %s)", (session['id'], symbol, quantity, datetime.now().date()))

					db.commit()
					flash('Transaction completed!')
				else:
					flash('Insufficient funds.')
					return render_template('trade.html', form=form)

			elif form.sell.data:

				#Check quantity
				cursor.execute("SELECT quantity FROM Stocks WHERE id=%s AND symbol=%s", (session['id'], symbol))
				owned = cursor.fetchone()[0]
				if owned:
					if quantity > owned:
						flash('You can\'t sell more stock than you own!')
						return render_template('trade.html', form=form)
					elif quantity == owned:
						cursor.execute("DELETE FROM Stocks WHERE id=%s AND symbol=%s", (session['id'], symbol))
					else:
						cursor.execute("UPDATE Stocks SET quantity=quantity-%s, date=%s WHERE id=%s AND symbol=%s", (quantity, datetime.now().date(), session['id'], symbol))

					#Increment cash
					cursor.execute("UPDATE Users SET cash=cash+%s WHERE id=%s", (trade_amount, session['id']))
					db.commit()
					flash('Transaction completed!')

				else:
					flash('You can\'t sell a stock you don\'t own!')
					return render_template('trade.html', form=form)

		except:
			flash('An error occurred.')
		return redirect(url_for('trade'))

	return render_template('trade.html', form=form)


@app.route('/research', methods=['GET','POST'])
def research():

	if 'loggedin' not in session:
		flash('Log In or Sign Up to start trading!')
		return redirect(url_for('login'))

	form = ResearchForm()

	if form.validate_on_submit():
		symbol = form.symbol.data.upper()
		#timeframe = form.timeframe.data

		try:
			return render_template('research.html', form=form, symbol=symbol)
		except:
			flash('It did not work...')

	return render_template('research.html', form=form)

def dayPeriodCloseLists(tickr):

    newTickr = yf.Ticker(tickr)
    dayMonthHist = newTickr.history(period='1y', interval='1d') # gets pandas DataFrame [date, open, high, low, close, vol, div, stock splits]
    print(dayMonthHist)
    dateValList = re.split("[ \n]+", dayMonthHist.iloc[:, 3].to_string()) # Formats DataFrame into parsable list of dates and close vals (splits by multiple spaces or newlines)
    datesList = dateValList[1::2]
    valList = (dateValList[2::2])
    print(datesList, valList)
    valNumList = []
    for val in valList:
        valNumList.append(float(val))

    # for i in range(1,len(dateValList)-1,2): # iterates dates and closes and assigns K/V relationship into dict
    #     dayMonthCloseDict[dateValList[i]] = dateValList[i+1]

    return datesList, valNumList # key = date | val = price

def conv(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').isoformat()

@app.route('/data')
def data():
    ''' Endpoint which returns jsonified data '''
    dates, prices = dayPeriodCloseLists("AAPL") # returns 'mm-dd-yyyy' string and float objects as two lists
    datePriceList =[dict(x=conv(date), y=prices[idx]) for idx,date in enumerate(dates)]

    d = {'datasets':
            [
                {'title': 'From Dict',
                 'data': datePriceList,
                },
            ],
        }
    return jsonify(d)

@app.route('/dynamic')
def dynamic():

    q = request.args.get('q')

    print (q)

    # You could dynamically build the following result now
    # based on the value of `q` which is passed from the frontend.
    # Here we just set that to the title.

    d = {'datasets':
            [
                {'title': q,
                 'data': sample_list,
                },
            ],
        }

    return jsonify(d)

@app.route('/portfolio', methods=['GET','POST'])
def portfolio():

	if 'loggedin' not in session:
		flash('Log In or Sign Up to start trading!')
		return redirect(url_for('login'))

	cursor.execute("SELECT * FROM Users WHERE id=%s", session['id'])
	for row in cursor:
		cash = row[4]

	cursor.execute("SELECT * FROM Stocks WHERE id=%s", session['id'])
	stocks = cursor.fetchall()

	portfolio = []
	portfolio_value = cash

	for row in stocks:
		symbol = row[1]
		quantity = row[2]
		price = Decimal(yf.Ticker(symbol).info['ask']).quantize(Decimal('.01'), rounding=ROUND_DOWN)
		total = Decimal(price*quantity).quantize(Decimal('.01'), rounding=ROUND_DOWN)
		portfolio.append((symbol, price, quantity, total, row[3]))
		portfolio_value += total

	return render_template('portfolio.html', portfolio=portfolio, portfolio_value=portfolio_value, cash=cash)

@app.route('/leaderboard')
def leaderboard():
	if 'loggedin' not in session:
		flash('Log In or Sign Up to start trading!')
		return redirect(url_for('login'))

	lb = []

	cursor.execute("SELECT * FROM Users")
	users = cursor.fetchall()
	for user in users:
		total = user[4]
		cursor.execute("SELECT * FROM Stocks WHERE id=%s", user[0])
		stocks = cursor.fetchall()
		for row in stocks:
			symbol = row[1]
			quantity = row[2]
			price = Decimal(yf.Ticker(symbol).info['ask']).quantize(Decimal('.01'), rounding=ROUND_DOWN)
			total += Decimal(price*quantity).quantize(Decimal('.01'), rounding=ROUND_DOWN)
		lb.append((total, user[2]))

	lb.sort(reverse=True)

	return render_template('leaderboard.html', lb=lb)
