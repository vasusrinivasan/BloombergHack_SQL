from flask import Flask
from flask.ext.mongoengine import MongoEngine

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': "my_tumble_log"}
app.config["SECRET_KEY"] = "\x07&\xda\xdc`:k\xa3\xeaC\xb86\x14\x1f\xd5\x9b\x9d\xb3\x1e\xf2\xc20\x07Y"

db = MongoEngine(app)

if __name__ == '__main__':
    app.run()