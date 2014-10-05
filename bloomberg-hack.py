from os.path import abspath, dirname, join
from flask import Flask, Markup, flash, url_for, render_template, redirect, session, request
from flask_sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from flask.ext.babel import Babel
from flask_user import current_user, login_required, UserManager, UserMixin, SQLAlchemyAdapter
from wtforms import fields
from wtforms.ext.sqlalchemy.fields import QuerySelectField

class ConfigClass(object):
    SECRET_KEY = '\x07&\xda\xdc`:k\xa3\xeaC\xb86\x14\x1f\xd5\x9b\x9d\xb3\x1e\xf2\xc20\x07Y'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + join(dirname(abspath(__file__)), 'bloomberg-hack.db')
    SQLALCHEMY_ECHO = True
    WTF_CSRF_SECRET_KEY = '\x18r*2\x91|\xa3(\x0b\xb7\xfao-\xf9b\xb2\x07{\xa6l'
    CSRF_ENABLED = True
    USER_ENABLE_EMAIL = False
    USER_ENABLE_RETYPE_PASSWORD = False
    USER_ENABLE_USERNAME = True
    USER_ENABLE_EMAIL  = False

app = Flask(__name__)
app.config.from_object(__name__+'.ConfigClass')

babel = Babel(app)
db = SQLAlchemy(app)

@babel.localeselector
def get_locale():
    translations = [str(translation) for translation in babel.list_translations()]
    return request.accept_languages.best_match(translations)

# Define User model. Make sure to add flask.ext.user UserMixin!!
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean(), nullable=False, default=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, default='')

db.create_all()

db_adapter = SQLAlchemyAdapter(db,  User)       # Select database adapter
user_manager = UserManager(db_adapter, app)     # Init Flask-User and bind to app

@app.route('/')
def landing_page(): 
    stock_form = StockForm()
    if 'username' in session:
      return render_template('home')
    return render_template('landing_page.html')


@app.route('/')
def home_page():
    return render_template_string("""
        {% extends "base.html" %}
        {% block content %}
            <h2>{%trans%}Home Page{%endtrans%}</h2>
            {% if current_user.is_authenticated() %}
            <p> <a href="{{ url_for('profile_page') }}">
                {%trans%}Profile Page{%endtrans%}</a></p>
            <p> <a href="{{ url_for('user.logout') }}">
                {%trans%}Sign out{%endtrans%}</a></p>
            {% else %}
            <p> <a href="{{ url_for('user.login') }}">
                {%trans%}Sign in or Register{%endtrans%}</a></p>
            {% endif %}
        {% endblock %}
        """)
    if current_user.is_authenticated():
        return redirect(url_for('home'))
    else:
        return redirect(url_for('user.login'))

# @app.route('/login', methods=['GET', 'POST'])
# def login(): 
#     error = None
#     if request.method == 'POST':
#         if request.form['username'] != 'admin' or \
#                 request.form['password'] != 'secret':
#             error = 'Invalid credentials'
#         else:
#             flash('You were successfully logged in')
#             return redirect(url_for('home'))
#     return render_template(url_for('login'), error=error)

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         # login and validate the user...
#         login_user(user)
#         flash("Logged in successfully.")
#         return redirect(request.args.get("next") or url_for("home"))
#     return render_template("login.html", form=form)

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('landing_page'))


@app.route("/settings")
@login_required
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

class UsersxStocks(db.Model):
    __tablename__ = 'subscribed_users'

    id = db.Column(db.Integer, primary_key=True)
    stock = db.Column(db.String)
    user_name = db.Column(db.String)



@app.route("/home")
def home():
    stock_form = StockForm()

    return render_template("index.html",
                           stock_form=stock_form)


@app.route("/stock", methods=("POST", ))
@login_required
def add_stock():
    form = StockForm()
    if form.validate_on_submit():
        def is_valid_stock(stock):
            db.session
        stock = Stock()
        if is_valid_stock(stock):
            form.populate_obj(stock)
            db.session.add(stock)
            db.session.commit()
            flash("Added stock " + form.stock_name.data)
        return redirect(url_for("view_stocks"))
    return render_template("validation_error.html", form=form)


@app.route("/porfolio")
@login_required
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
