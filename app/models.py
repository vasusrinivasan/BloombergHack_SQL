from flask import Flask, flash, url_for, render_template
from app import db

class User(db.Document):
	user_id = db.StringField(required=True)
	password = db.StringField(required=True)
	number = db.StringField(required=True)
	carrier = db.StringField(required=True)
	stock_list = db.ListField()

    def db_get_user_id(self):
    	return self.user_id

    def db_get_password(self):
    	return self.password

    def db_get_number(self):
    	return self.number

    def db_get_carrier(self):
    	return self.carrier

    def db_get_stock_list(self):
    	return self.stock_list

class Stock(db.Document):
    ticker_id = db.StringField(required=True)
    user_list = db.ListField()