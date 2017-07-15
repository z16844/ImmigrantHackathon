#/usr/bin/python
# _*_ coding: utf8 _*_

from flask import request, render_template,  jsonify
from werkzeug import secure_filename
from Flask_ImmigrantHackathon import app, mysql, UPLOAD_PATH
from model import GeoLocation, Messege
import requests,httplib,urllib,time
import os,math, json
import pdb

GOOGLE_MAPS_API_KEY = ""

PUSHOVER_USERKEY = ""
PUSHOVER_APIKEY = ""

def alert(title, messages):
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST","/1/messages.json",
            urllib.urlencode({
                "token": PUSHOVER_APIKEY,
                "user":PUSHOVER_USERKEY ,
                "title":title,
                "message": messages,
                "priority":1,
                "timestamp":int(time.time()),
                #'sound': sound
                }),{"Content-type":"application/x-www-form-urlencoded"})
    conn.getresponse()

def GetDistance(p1,p2):
	url = "https://maps.googleapis.com/maps/api/distancematrix/json"
	querystring = {"key":GOOGLE_MAPS_API_KEY,"origins":str(p1[0]) + "," + str(p1[1]),"destinations":str(p2[0]) + "," + str(p2[1])}
	response = requests.request("GET", url, params=querystring).json()
	if response["rows"][0]["elements"][0]["status"] == "ZERO_RESULTS":
		return None
	else:
		return response["rows"][0]["elements"][0]["distance"]

def GetClosestObject(p1,GeoLocList):
	result = {}
	for item in GeoLocList:
		DistanceInfo = GetDistance((float(p1.Latitude),float(p1.Longitude)),(float(item.Latitude),float(item.Longitude)))
		if DistanceInfo is None:
			continue
		result[float(DistanceInfo["value"])] = (DistanceInfo["text"], item);
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
			# newPost.Anonymous = request.form["Anonymous"] == 1
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
			alert(newPost.Auther,newPost.Messege) # to proof concept
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

	distanceKM = float(ClosestPoint[0].split(' ')[0])

	SQL = "SELECT * FROM Messege WHERE GeoLocationKey=%d" % ClosestPoint[1].GeoLocationKey
	cursor.execute(SQL)

	columns = tuple( [d[0] for d in cursor.description] )
	rows = []
	for row in cursor:
		rows.append(dict(zip(columns,row)))

	row = rows[0]

	if(distanceKM<1.0):
		alert(row["Auther"],row["Messege"])
	Model = {"Messege":row["Messege"],"Auther":row["Auther"],"attachmentFiles":row["attachmentFiles"],"anonymous":row["anonymous"],"Latitude":ClosestPoint[1].Latitude,"Longitude":ClosestPoint[1].Longitude,"Distance":ClosestPoint[0]}
	return jsonify(Model)


@app.errorhandler(404)
def NotFound():
	return "Http/1.1 404 Not Found"

@app.errorhandler(500)
def InternalError():
	return "Http/1.1 500 Internal Error"