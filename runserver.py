#/usr/bin/python
# _*_ coding: utf8 _*_

from Flask_ImmigrantHackathon import app
import os

if __name__ == "__main__":
	app.config["MYSQL_DATABASE_HOST"] = "commuter.tachyon.network"
	app.run(debug=True,host='127.0.0.1',port=5555)