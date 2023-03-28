import json
from flask import jsonify, render_template, Response, request, make_response, url_for, redirect
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, set_access_cookies
import datetime
from helper import *
import hashlib

from app import app, db, mongodb
from forms import LoginForm, SignupForm

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
                res = Response(status=200)
                set_access_cookies(res, jwt_token)
                return res
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

@app.route("/statements", methods=("POST", "GET"))
@jwt_required()
def statements():
    username = json.loads(get_jwt_identity())["user"]
    transactions = list(db["TRANSACTIONS"].find(
            {"$or": [{'FROM': username}, {'TO': username}]},
            {'_id': False}))
    if request.method == 'POST':
        return jsonify({'transactions': transactions})
    elif request.method == 'GET':
        return render_template("statements.html", transactions=transactions)

@app.route("/transfer", methods=("GET", "POST"))
@jwt_required()
def transfer():
    if request.method == 'GET':
        success = request.args.get('success') or False
        return render_template("transfer.html", success=success)

    user_from = json.loads(get_jwt_identity())["user"]

    user_to = request.form.get("user_to")
    amount = int(request.form.get("amount"))
    remark = request.form.get("remark") or ''

    if db["USERS"].count_documents({'USR_NAME': user_to}) == 0: return Response(status=400)
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

    return redirect(url_for('transfer', success=True))

@app.route("/signup", methods=("POST",))
def signup():
    form = SignupForm(request.form)

    if form.validate():
        username = request.form["username"]
        query = db["USERS"].find_one({ "USR_NAME" : username })
        if query is not None:
            return Response(status=400)

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        if password != confirm_password:
            return Response(status=400)
        
        pincode = request.form["pin"]
        pin_query = db["PINCODE"].find_one({"Pincode": pincode})
        if pin_query is None:
            return Response(status=400)
        
        db["USERS"].insert_one({
            'USR_NAME': request.form["username"],
            'NAME': request.form["name"],
            'PASS': hashlib.sha256(request.form["password"].encode()).hexdigest(),
            'PHONE': request.form["phone"],
            'PAN': request.form["pan"],
            'PIN': request.form["pin"],
            'VOTE_REGION': pin_query["StateName"],
            'ACC_TYPE': request.form["account_type"],
            'USR_TYPE': "regular",
            'BLANCE': 0,
        })

        return Response(status=200)
    return Response(status=400)
