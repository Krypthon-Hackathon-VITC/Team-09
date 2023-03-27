import json
from app import app, db
from flask import jsonify, render_template, Response, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import hashlib

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/login", methods=("POST",))
def login():
    flag = False
    try:
        username = request.form.get("username")
        password = request.form.get("password")
        password = hashlib.sha256(password.encode()).hexdigest()
        query = db["USERS"].find_one({ "USR_NAME" : username })
        if query["PASS"].lower() == password.lower():
            flag = True
    except:
        flag = False
    if flag:
        jwt_token = create_access_token(identity=json.dumps({"user":username}))
        return jsonify(jwt_token)
    else:
        return Response(status=400)

@app.route("/dashboard")
@jwt_required()
def bank():
    username = json.loads(get_jwt_identity())["user"]
    query = db["USERS"].find_one({"USR_NAME" : username})
    role = query["USR_TYPE"]
    return render_template("dashboard.html", role=role)