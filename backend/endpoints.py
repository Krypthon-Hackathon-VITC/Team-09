import json
from app import app, db
from flask import jsonify, render_template, Response, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from datetime import datetime
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
        return jsonify({'token': jwt_token})
    else:
        return Response(status=400)

@app.route("/dashboard")
@jwt_required()
def bank():
    username = json.loads(get_jwt_identity())["user"]
    query = db["USERS"].find_one({"USR_NAME" : username})
    role = query["USR_TYPE"]
    return render_template("dashboard.html", role=role)

@app.route("/balance", methods=("POST",))
@jwt_required()
def balance():
    username = json.loads(get_jwt_identity())["user"]
    query = db["USERS"].find_one({"USR_NAME" : username})
    return jsonify({'balance': query['BALANCE']})

@app.route("/statements", methods=("POST",))
@jwt_required()
def statements():
    username = json.loads(get_jwt_identity())["user"]
    transactions = list(db["TRANSACTIONS"].find(
            {"$or": [{'FROM': username}, {'TO': username}]},
            {'_id': False}))
    return jsonify({'transactions': transactions})
