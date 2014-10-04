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

class Portfolio(db.Model):
    __tablename__ = 'tracking_site'

    id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String)
    stock_news = db.Column(db.String)
    ticker_data = db.Column(db.String)

    def __repr__(self):
        return '<Site %r>' % (self.stock_name)

    def __str__(self):
        return self.stock_name

class StockForm(Form):
    name = fields.StringField()
    news = fields.StringField()
    ticker_data = fields.StringField()
    stock = QuerySelectField(query_factory=Portfolio.query.all)

@app.route("/")
def index():
    stock_form = StockForm()
    return render_template("index.html",
                           site_form=stock_form)


@app.route("/site", methods=("POST", ))
def add_site():
    form = StockForm()
    if form.validate_on_submit():
        site = Site()
        form.populate_obj(site)
        db.session.add(site)
        db.session.commit()
        flash("Added site")
        return redirect(url_for("index"))
    return render_template("validation_error.html", form=form)


@app.route("/sites")
def view_sites():
    query = Site.query.filter(Site.id >= 0)
    data = query_to_list(query)
    data = [next(data)] + [[_make_link(cell) if i == 0 else cell for i, cell in enumerate(row)] for row in data]
    return render_template("data_list.html", data=data, type="Sites")


_LINK = Markup('<a href="{url}">{name}</a>')


def _make_link(site_id):
    url = url_for("view_site_visits", site_id=site_id)
    return _LINK.format(url=url, name=site_id)


@app.route("/site/<int:site_id>")
def view_site_visits(site_id=None):
    site = Site.query.get_or_404(site_id)
    query = Visit.query.filter(Visit.site_id == site_id)
    data = query_to_list(query)
    title = "visits for " + site.name
    return render_template("data_list.html", data=data, type=title)


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
