# db_get_FIELD

FAILURE = 1
SUCCESS = 0

import pymongo
from pymongo import MongoClient

# Global Database Variables
client = None
db = None
col_user_info = None
col_ticker = None

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
		col_ticker = db['ticker']
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
def db_put_user(user_id, password, phone, carrier, stock_list = []):
	phone = __helper_clean_number(phone) # Clean!
	new_user = {'user_id'	:	user_id,
				'password'	:	password,
				'number'	:	phone,
				'carrier'	:	carrier,
				'stock_list':	[]}
	col_user_info.insert(new_user)
	return SUCCESS

def __helper_clean_number(input_num):
	retVal = ""
	for each in input_num:
		if (each.isdigit()): retVal += each
	return retVal



"""
def db_valid_username(user_id)

Checks whether a given username (user_id) is valid
Invalid if someone else has already taken it

	<String> user_id	proposed username

	RETURNS: true (valid) or false (invalid)
"""
def db_valid_username(user_id):
	if(col_user_info.find({'user_id' : user_id}).count() > 0):
		return False
	else:
		return True


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
	ticker = ticker.upper() # Make upper case
	ticker = ticker.strip() # Trim
	stock_list = db_get_stocks(user_id)
	if (ticker not in stock_list):
		stock_list.append(ticker)
		col_user_info.update(
			{'user_id'		: user_id},
			{'user_id'		: user_id,
			 'stock_list'	: stock_list})
	__helper_db_addstock(user_id, ticker)
	return SUCCESS



"""
def __helper_db_addstock(user_id, ticker)

Internal helper function. USER SHOULD NOT USE.
Adds a user to a ticker's list of subscribers
	<String> user_id	user_id
	<String> ticker 	stock ticker

	RETURNS SUCCESS (0) OR FAILURE (1)
"""
def __helper_db_addstock(user_id, ticker):
	ticker = ticker.upper() # Make upper case
	ticker = ticker.strip() # Trim
	if (col_ticker.find({'ticker' : ticker}).count() == 0):
		# Does not exist, add the stock
		new_stock = {'ticker'	:	ticker,
					 'user_list':	[user_id]}
		col_ticker.insert(new_stock)
	else:
		# Stock already exists, just add the user
		user_list = db_get_subscribers(ticker)
		if (user_id not in user_list):
			user_list.append(user_id)
			col_ticker.update(
				{'ticker_id'	: ticker},
				{'ticker_id'	: ticker,
				 'user_list'	: user_list})
	return SUCCESS



"""
db_get_stocks(user_id)

Looks up a user_id, and finds all the stocks that they are subscripted too

	<String> user_id	username

	RETURNS: <list> of stocks (as tickers) that the user is subscribed to
"""
def db_get_stocks(user_id):
	return col_user_info.find_one({'user_id' : user_id})['stock_list']

"""
db_get_subscribers(ticker)

Takes a stock (as a ticker), and finds all its subscribed users.

	<String> ticker 	stock's ticker

	RETURNS: <list> of users that are subscribed to a ticker
"""
def db_get_subscribers(ticker):
	if (col_ticker.find({'ticker' : ticker}).count() == 0):
		return []
	else:
		return col_ticker.find_one({'ticker' : ticker})['user_list']



"""
db_get_number(user_id)

Looks up a user_id, and finds user's number and carrier

	<String> user_id	username

	RETURNS: <tuple> (number, carrier) of user, both are strings
"""
def db_get_number(user_id):
	doc = col_user_info.find_one({'user_id' : user_id})
	return (str(doc['number']), str(doc['carrier']))
	

# WARNING: No safety checks
def db_get_user_obj(user_id):
	if(col_user_info.find({'user_id' : user_id}).count() == 0):
		return None
	else:
		return col_user_info.find_one({'user_id' : user_id})

if __name__ == '__main__':
	__init__()