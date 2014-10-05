from os.path import abspath, dirname, join
from flask import Flask, Markup, flash, url_for, render_template, redirect, session, request
from flask_sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from flask.ext.login import LoginManager
from wtforms import fields
from wtforms.ext.sqlalchemy.fields import QuerySelectField

_cwd = dirname(abspath(__file__))
login_manager = LoginManager()

SECRET_KEY = '\x07&\xda\xdc`:k\xa3\xeaC\xb86\x14\x1f\xd5\x9b\x9d\xb3\x1e\xf2\xc20\x07Y'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + join(_cwd, 'bloomberg-hack.db')
SQLALCHEMY_ECHO = True
WTF_CSRF_SECRET_KEY = '\x18r*2\x91|\xa3(\x0b\xb7\xfao-\xf9b\xb2\x07{\xa6l'

app = Flask(__name__)
app.config.from_object(__name__)
login_manager.init_app(app)

db = SQLAlchemy(app)

@login_manager.user_loader
def load_user(userid):
    return User.query.get(int(id))

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
    return redirect(url_for('home'))


@app.route("/settings")
def settings():
    pass

class Stock(db.Model):
    __tablename__ = 'stock_entry'

    id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String)
    # stock_news = db.Column(db.String)
    # ticker_data = db.Column(db.String)

    def __repr__(self):
        return '<Stock %r>' % (self.stock_name)

    def __str__(self):
        return self.stock_name

class StockForm(Form):
    stock_name = fields.StringField()

@app.route('/')
def landing_page(): 
    stock_form = StockForm()
    if 'username' in session:
      return 'Logged in as %s' % escape(session['username'])
    return render_template('landing_page.html')

@app.route("/home")
def home():
    stock_form = StockForm()

    return render_template("index.html",
                           stock_form=stock_form)


@app.route("/stock", methods=("POST", ))
def add_stock():
    form = StockForm()
    if form.validate_on_submit():
        stock = Stock()
        form.populate_obj(stock)
        db.session.add(stock)
        db.session.commit()
        flash("Added stock " + form.stock_name.data)
        return redirect(url_for("view_stocks"))
    return render_template("validation_error.html", form=form)


@app.route("/porfolio")
def view_stocks():
    query = Stock.query.filter(Stock.id >= 0)
    data = query_to_list(query)
    data = [next(data)] + [[cell for i, cell in enumerate(row)] for row in data]
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
    db.create_all()
    app.run()
