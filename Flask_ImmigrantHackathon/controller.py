#/usr/bin/python
# _*_ coding: utf8 _*_

from flask import request, render_template,  jsonify
from werkzeug import secure_filename
from Flask_ImmigrantHackathon import app, mysql, UPLOAD_PATH
from model import GeoLocation, Messege
import os,math
import pdb

def GetDistance(p1,p2):
	return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
def GetClosestObject(p1,GeoLocList):
	result = {}
	for item in GeoLocList:
		result[GetDistance((float(p1.Latitude),float(p1.Longitude)),(float(item.Latitude),float(item.Longitude)))] = item;
	closestDistance = min(result.keys())
	return result[closestDistance]

@app.route('/',methods=["GET","POST"])
def index():
	try:
		conn = mysql.connect()
		cursor = conn.cursor()
		if request.method == "GET":
			SQL = ""
			return render_template("index.html")
		elif request.method == "POST":
			newGeoLoc = GeoLocation()
			newGeoLoc.Latitude = float(request.form["Latitude"])
			newGeoLoc.Longitude = float(request.form["Longitude"])
			SQL = "INSERT INTO GeoLocation (`Latitude`, `Longitude`) VALUES ( %f,%f);" % (newGeoLoc.Latitude,newGeoLoc.Longitude)
			cursor.execute(SQL)
			newGeoLoc.GeoLocationKey = cursor.lastrowid

			newPost = Messege()
			newPost.Messege = request.form["Messege"]
			newPost.Auther = request.form["Auther"]
			newPost.Anonymous = request.form["Anonymous"] == 1
			newPost.GeoLocationKey = newGeoLoc.GeoLocationKey
			if "files" in request.files:
				fileList = []
				for file in request.files.getlist("files"):
					secureFilename = secure_filename(file.filename)
					fileList.append(secureFilename)
					file.save(os.path.join(UPLOAD_PATH,secureFilename))
				newPost.AttachmentFiles = "|||".join([str(item) for item in fileList])
			SQL = """INSERT INTO Messege (`Messege`, `Auther`, `attachmentFiles`, `anonymous`, `GeolocationKey`) VALUES ( '%s', '%s', '%s', '%d', %d); """ % (newPost.Messege,newPost.Auther,newPost.AttachmentFiles,newPost.Anonymous,newPost.GeoLocationKey)
			cursor.execute(SQL)
			conn.commit()
			return "success"
	except Exception:
		return InternalError()

@app.route('/closestSpot',methods=["GET"])
def closestSpot():
	conn = mysql.connect()
	cursor = conn.cursor()

	currentPosition = GeoLocation()
	currentPosition.Latitude = request.args.get("Latitude")
	currentPosition.Longitude = request.args.get("Longitude")

	SQL = "SELECT * FROM GeoLocation"
	cursor.execute(SQL)

	result = []
	for item in cursor.fetchall():
		tmpModel = GeoLocation();
		tmpModel.GeoLocationKey = int(item[0])
		tmpModel.Latitude = float(item[1])
		tmpModel.Longitude = float(item[2])
		result.append(tmpModel)
	ClosestPoint = GetClosestObject(currentPosition,result)

	SQL = "SELECT * FROM Messege WHERE GeoLocationKey=%d" % ClosestPoint.GeoLocationKey
	cursor.execute(SQL)

	pdb.set_trace()
	columns = tuple( [d[0] for d in cursor.description] )
	rows = []
	for row in cursor:
		rows.append(dict(zip(columns,row)))

	row = rows[0]

	Model = {"Messege":row["Messege"],"Auther":row["Auther"],"attachmentFiles":row["attachmentFiles"],"anonymous":row["anonymous"],"Latitude":ClosestPoint.Latitude,"Longitude":ClosestPoint.Longitude, }
	return jsonify(Model)


@app.errorhandler(404)
def NotFound():
	return "Http/1.1 404 Not Found"

@app.errorhandler(500)
def InternalError():
	return "Http/1.1 500 Internal Error"