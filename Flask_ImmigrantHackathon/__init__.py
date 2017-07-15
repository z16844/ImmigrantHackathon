#/usr/bin/python
# _*_ coding: utf8 _*_

from flask import Flask
from flaskext.mysql import MySQL
import os
UPLOAD_PATH = os.path.abspath("./Flask_ImmigrantHackathon/static/Upload") + "/"

app = Flask(__name__, static_url_path='/static')
mysql = MySQL();

app.config["MYSQL_DATABASE_USER"] = "hackathon"
app.config["MYSQL_DATABASE_PASSWORD"] = "hackathon"
app.config["MYSQL_DATABASE_DB"] = "hackathon"

app.config['UPLOAD_FOLDER'] = UPLOAD_PATH

mysql.init_app(app)


import model
import controller