from os.path import abspath, dirname, join
from flask import Flask, Markup, flash, url_for, render_template, redirect, session, request
from flask_sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from wtforms import fields
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask.ext.mongoengine import MongoEngine

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': "my_tumble_log"}
app.config["SECRET_KEY"] = "\x07&\xda\xdc`:k\xa3\xeaC\xb86\x14\x1f\xd5\x9b\x9d\xb3\x1e\xf2\xc20\x07Y"

db = MongoEngine(app)


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

class StockForm(Form):
    stock_name = fields.StringField()

@app.route('/')
def landing_page(): 
    stock_form = StockForm()
    if 'username' in session:
      return render_template('home')
    return render_template('landing_page.html')

@app.route('/login', methods=['GET', 'POST'])
def login(): 
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or \
                request.form['password'] != 'secret':
            error = 'Invalid credentials'
        else:
            flash('You were successfully logged in')
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('landing_page'))


@app.route("/settings")
def settings():
    pass

@app.route("/home")
def home():
    stock_form = StockForm()
    return render_template("index.html",
                           stock_form=stock_form)


@app.route("/stock", methods=("POST", ))
def add_stock():
    form = StockForm()
    if form.validate_on_submit():
        db.db_put_subscriber()
        flash("Added stock " + form.stock_name.data)
        return redirect(url_for("view_stocks"))
    return render_template("validation_error.html", form=form)


@app.route("/porfolio")
def view_stocks():
    data = db.db_get_stocks
    return render_template("data_list.html", data=data, type="Stocks")

def query_to_list(query, include_field_names=True):
    """Turns a SQLAlchemy query into a list of data values."""
    column_names = []
    for i, obj in enumerate(query.all()):
        if i == 0:
            column_names = [c.name for c in obj.__table__.columns]
            if include_field_names:
                yield column_names
        yield obj_to_list(obj, column_names)


def obj_to_list(sa_obj, field_order):
    """Takes a SQLAlchemy object - returns a list of all its data"""
    return [getattr(sa_obj, field_name, None) for field_name in field_order]

if __name__ == "__main__":
    app.debug = True
    app.run()
