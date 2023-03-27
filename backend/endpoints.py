import json
from app import app, db, mongodb
from flask import jsonify, render_template, Response, request, redirect, url_for
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import datetime
from helper import *
import hashlib

from forms import LoginForm

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/login", methods=("POST", "GET"))
def login():
    form = LoginForm(request.form)

    if form.validate():
        username = request.form["username"]
        password = request.form.get("password")
        password = hashlib.sha256(password.encode()).hexdigest()
        query = db["USERS"].find_one({ "USR_NAME" : username })
        if query is not None:
            if query["PASS"].lower() == password.lower():
                jwt_token = create_access_token(identity=json.dumps({"user":username}))
                return jsonify(jwt_token)
        else:
            return Response(status=401)

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
    return jsonify({'balance': get_balance(username)})

@app.route("/statements", methods=("POST",))
@jwt_required()
def statements():
    username = json.loads(get_jwt_identity())["user"]
    transactions = list(db["TRANSACTIONS"].find(
            {"$or": [{'FROM': username}, {'TO': username}]},
            {'_id': False}))
    return jsonify({'transactions': transactions})

@app.route("/transfer", methods=("POST",))
@jwt_required()
def transfer():
    user_from = json.loads(get_jwt_identity())["user"]

    user_to = request.form.get("user_to")
    amount = int(request.form.get("amount"))
    remark = request.form.get("remark") or ''

    if db["USERS"].count_documents({'USR_NAME': user_to}) == 0:
        return Response(status=400)

    from_bal = get_balance(user_from)
    to_bal = get_balance(user_to)

    if amount > from_bal:
        return Response(status=400)

    with mongodb.start_session() as session:
        with session.start_transaction():
            db["USERS"].update_one({'USR_NAME': user_from},
                    {'$set': {'BALANCE' : from_bal - amount}})
            db["USERS"].update_one({'USR_NAME': user_to},
                    {'$set': {'BALANCE' : to_bal + amount}})

            db["TRANSACTIONS"].insert_one(
                    {'TIME': datetime.datetime.now(),
                        'FROM': user_from,
                        'TO': user_to,
                        'AMOUNT': amount,
                        'REMARK': remark})

    return Response(status=200)
