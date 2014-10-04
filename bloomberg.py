from os.path import abspath, dirname, join

from flask import Flask, Markup, flash, url_for, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from wtforms import fields
from wtforms.ext.sqlalchemy.fields import QuerySelectField

_cwd = dirname(abspath(__file__))

SECRET_KEY = '\x07&\xda\xdc`:k\xa3\xeaC\xb86\x14\x1f\xd5\x9b\x9d\xb3\x1e\xf2\xc20\x07Y'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + join(_cwd, 'bloomberg-hack.db')
SQLALCHEMY_ECHO = True
WTF_CSRF_SECRET_KEY = '\x18r*2\x91|\xa3(\x0b\xb7\xfao-\xf9b\xb2\x07{\xa6l'


app = Flask(__name__)
app.config.from_object(__name__)
db = SQLAlchemy(app)

# class Site(db.Model):
# 	__tablename__ = 'ticker_watch_site'

# 	id = db.Column(db.Integer, primary_key=True)
# 	base_url = db.Column(db.String)
# 	visits = db.relationship('Visit', backref='ticker_watch_site', lazy='select')

# 	def __repr__(self):
# 		return '<Site %r>' % (self.base_url)

# 	def __str__(self):
# 		return self.base_url

class Stock(db.Model):
	__tablename__ = 'stock_portfolio'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	news = db.Column(db.String)
	ticker_data = db.Column(db.String)

	def __repr__(self):
		return 'Stock %r>' % (self.name)

	def __str__(self):
		return self.name

class StockForm(Form):
	stock_name = fields.StringField()
	news = fields.StringField()
	ticker_data = fields.StringField()
	base_url = fields.StringField()
	stock = QuerySelectField(query_factory=Stock.query.all)


@app.route('/')
def index(): 
	stock_form = StockForm()
	if 'username' in session:
		return render_template('index.html', stock_form=stock_form)
	return render_template('index.html', stock_form=stock_form)
	# 	return 'Logged in as %s' % escape(session['username'])
	# return 'You are not logged in'
	# return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login(): 
	error = None
	# if request.method == 'POST':
	# 	session['username'] = request.form['username']
	# 	return redirect(url_for('index'))
	return '''
		<form action="" method="post">
			<p>Username: <input type=text name=username>
			<p>Password: <input type=text name=password>
			<p><input type=submit value=Login>
		</form>
	'''
	# 	if valid_login(request.form['username'], request.form['password']):
	# 		return log_the_user_in(request.form['username'])
	# else:
	# 	error = 'Invalid username/password'
	return render_template('hello.html', error = error)

@app.route('/stock', methods=['POST',])
def add_stock():
	form = StockForm()
	if form.validate_on_submit():
		stock = Stock()
		form.populate_obj(stock)
		db.session.add(stock)
		db.session.commit()
		flash('Added stock to your portfolio ' + form.stock.name)
	return render_template('validation_error.html', form=form)

@app.route('/portfolio')
def view_portfolio():
	query = Stock.query.filter(Stock.id >= 0)
	data = query_to_list(query)
	data = [next(data)] + [[cell for i, cell in enumerate(row) for row in data]]
	return render_template("data_list.html", data=data, type="Portfolio")


@app.route('/user/<username>')
def profile(username):
	return 'User %s' % username


@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for('index'))

def query_to_list(query, include_field_names=True):
	column_names = []
	for i, obj in enumerate(query.all()):
		if i == 0:
			column_names = [c.name for c in obj.__table__.columns]
			if include_field_names:
				yield column_names
		yield obj_to_list(obj, column_names)

def obj_to_list(sa_obj, field_order):
	return [getattr(sa_obj, field_name, None) for field_name in field_order]

# with app.test_request_context():
# 	print url_for('index')
# 	print url_for('login')
# 	print url_for('login', next='/')
# 	print url_for('profile', username='John Doe')

if __name__ == '__main__':
	app.debug = True
	db.create_all()
	app.run()
