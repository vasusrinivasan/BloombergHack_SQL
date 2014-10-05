FAILURE = 1
SUCCESS = 0

import pymongo
from pymongo import MongoClient

# Global Database Variables
client = None
db = None

"""
Initializer.
"""
def __init__():
	client = MongoClient('localhost', 27017)
	# URL format is MongoClient('mongodb://localhost:27017/')
	if (client == None):
		print "ERROR: MongoClient COULD NOT CONNECT. EXITING"
		return FAILURE
	else:
		db = client['primary_database']
		col_user_info = db['user_info']
		col_user_stocks = db['user_stocks']
		col_ticker_subscribers = db['ticker']
		print "MongoClient has successfully connected"
		return SUCCESS

"""
def db_put_user(user_id, password, phone, carrier)

Adds a new user to the database
	<String> user_id	proposed username. note: this method does not check
						for uniqueness
	<String> passowrd
	<String> phone		phone number (does not need to be formatted)
	<String> carrier	select from one:
						att, at&t, verizon, boost, virgin

	RETURNS SUCCESS (0) OR FAILURE (1)
"""
def db_put_user(user_id, password, phone, carrier):
	pass



"""
def db_put_subscriber(ticker, user_id)

Subscribers a user to a ticker
	-> Ticker is now on user's list of subscriptions
	-> User gets added to ticker's subscribers (called via helper)

	<String> ticker 	stock ticker
	<String> user_id	user_id

	RETURNS SUCCESS (0) OR FAILURE (1)
"""
def db_put_subscriber(ticker, user_id):
	pass



"""
def __helper_db_addstock(user_id, ticker)

Internal helper function. USER SHOULD NOT USE.
Adds a user to a ticker's list of subscribers
	<String> user_id	user_id
	<String> ticker 	stock ticker

	RETURNS SUCCESS (0) OR FAILURE (1)
"""
def __helper_db_addstock(user_id, ticker):
	pass	



"""
def db_valid_username(user_id)

Checks whether a given username (user_id) is valid
Invalid if someone else has already taken it

	<String> user_id	proposed username

	RETURNS: true (valid) or false (invalid)
"""
def db_valid_username(user_id):
	pass



"""
db_get_stocks(user_id)

Looks up a user_id, and finds all the stocks that they are subscripted too

	<String> user_id	username

	RETURNS: <list> of stocks (as tickers) that the user is subscribed to
"""
def db_get_stocks(user_id):
	pass

"""
db_get_subscribers(ticker)

Takes a stock (as a ticker), and finds all its subscribed users.

	<String> ticker 	stock's ticker

	RETURNS: <list> of users that are subscribed to a ticker
"""
def db_get_subscribers(ticker):
	pass



"""
db_get_number(user_id)

Looks up a user_id, and finds user's number and carrier

	<String> user_id	username

	RETURNS: <tuple> (number, carrier) of user, both are strings
"""
def db_get_stocks(user_id):
	pass
	