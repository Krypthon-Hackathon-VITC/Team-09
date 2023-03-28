from bson import ObjectId
from flask import jsonify, render_template, Response, request, \
    make_response, url_for, redirect
from flask_jwt_extended import create_access_token, get_jwt_identity, \
    jwt_required, set_access_cookies, get_jwt
from helper import *

import datetime
import hashlib
import json
import uuid

from app import app, db, mongodb, MODEL, jwt
from forms import LoginForm, SignupForm, ComplaintForm, ElectionStand, \
    ElectionsVote, LoanForm, TransferForm


@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.datetime.now(datetime.timezone.utc)
        target_timestamp = datetime.timestamp(
            now + datetime.timedelta(minutes=15))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response


@app.route("/")
def homepage():
    return render_template("index.html", indexhai=True)


@app.route("/login", methods=("POST",))
def login():
    form = LoginForm(request.form)
    if form.validate():
        username = form["username"].data
        password = form["password"].data
        query = db["USERS"].find_one({"USR_NAME": username})
        if query is not None:
            hash = query["PASS"]
            if check_password_hash(password, hash):
                jwt_token = create_access_token(
                    identity=json.dumps({"user": username}))
                response = make_response(redirect(url_for('bank')))
                set_access_cookies(response, jwt_token)
                return response
        else:
            return Response(status=401)

    return Response(status=400)


@app.route("/dashboard")
@jwt_required()
def bank():
    user = get_jwt_user_object()
    role = user["USR_TYPE"]
    return render_template("dashboard.html", role=role)


@app.route("/balance", methods=("POST",))
@jwt_required()
def balance():
    username = get_jwt_username()
    return {'balance': get_balance_from_username(username)}


@app.route("/statements", methods=("POST", "GET"))
@jwt_required()
def statements():
    username = get_jwt_username()
    transactions = list(db["TRANSACTIONS"].find(
        {"$or": [{'FROM': username}, {'TO': username}]},
        {'_id': False}))
    if request.method == 'POST':
        return {'transactions': transactions}
    elif request.method == 'GET':
        return render_template("statements.html", transactions=transactions)


@app.route("/transfer", methods=("GET", "POST"))
@jwt_required()
def transfer():
    form = TransferForm(request.form)

    if form.validate():
        user_from = get_jwt_username()
        user_to = form["user_to"].data
        amount = form["amount"].data
        remark = form["remark"].data

        if user_to == user_from:
            return render_template('transfer.html', error="Cannot transfer \
                                                           money to self!")

        if amount <= 0:
            return render_template('transfer.html', error="Amount cannot be \
                                                           negative or zero!")

        check_user_to_query = db["USERS"].find_one({"USR_NAME": user_to})
        if check_user_to_query is None:
            return render_template('transfer.html', error="User does not exist!")

        from_bal = get_balance_from_username(user_from)
        to_bal = get_balance_from_username(user_to)

        if amount > from_bal:
            return render_template("transfer.html", error="Insufficient balance!")

        with mongodb.start_session() as session:
            with session.start_transaction():
                db["USERS"].update_one({'USR_NAME': user_from},
                                       {'$set': {'BALANCE': from_bal - amount}})
                db["USERS"].update_one({'USR_NAME': user_to},
                                       {'$set': {'BALANCE': to_bal + amount}})

                db["TRANSACTIONS"].insert_one({
                    'TIME': datetime.datetime.now(),
                    'FROM': user_from,
                    'TO': user_to,
                    'AMOUNT': amount,
                    'REMARK': remark
                })

        return render_template('transfer.html', success="Payment successful!")

    return render_template("transfer.html")


@app.route("/election")
def election():
    query = db["ELECTIONS"].find_one()
    if query is not None:
        election_date = query["ANNOUNCEMENT_DATE"]
        election_date = election_date.strftime("%d %b, %Y %H:%M:%S")
        return render_template("election.html", next_election=election_date)

    return render_template("election.html")


@app.route("/complaint", methods=("GET", "POST"))
@jwt_required()
def complaint():
    if request.method == "GET":
        success = request.args.get('success') or False
        error = request.args.get('error') or False
    username = json.loads(get_jwt_identity())["user"]
    tickets = list(db["TICKETS"].find({'FROM': username}))
    if request.method == "POST":
        return jsonify({'tickets': tickets})
    return render_template("complaint.html", complaints=tickets, success=success, error=error)


@app.route("/new-ticket", methods=("POST",))
@jwt_required()
def new_ticket():
    form = ComplaintForm(request.form)

    if form.validate():
        username = json.loads(get_jwt_identity())["user"]
        subject = request.form["subject"]
        body = request.form["body"]
        db["TICKETS"].insert_one({
            "FROM": username,
            "SUBJECT": subject,
            "BODY": body,
            "TIME": datetime.datetime.now(),
            "STATUS": False,
            "TICKET_ID": str(uuid.uuid4()).replace("-", ""),
            "REPLY": ""
        })

        return redirect(url_for('complaint', success=True))
    return redirect(url_for('complaint', success=False))


@app.route("/signup", methods=("POST",))
def signup():
    form = SignupForm(request.form)

    if form.validate():
        username = request.form["username"]
        query = db["USERS"].find_one({"USR_NAME": username})
        if query is not None:
            return Response(status=400)

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        if password != confirm_password:
            return Response(status=400)

        pincode = request.form["pin"]
        pin_query = db["PINCODE"].find_one({"Pincode": pincode})
        if pin_query is None:
            return Response(status=410)

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
            'BALANCE': 0,
        })

        return Response(status=200)
    return Response(status=411)


@app.route("/election/stand", methods=("POST", "GET"))
@jwt_required()
def election_stand():
    username = json.loads(get_jwt_identity())["user"]
    user = db["USERS"].find_one({"USR_NAME": username})

    election = str(db["ELECTIONS"].find_one({})["_id"])

    check_query = db["CANDIDATES"].find_one({
        "CANDIDATE_ID": str(user["_id"]),
        "ELECTION_ID": election
    })

    form = ElectionStand(request.form)

    if form.validate():
        username = json.loads(get_jwt_identity())["user"]
        user = db["USERS"].find_one({"USR_NAME": username})

        pw_hash = hashlib.sha256(request.form.get(
            "password").encode()).hexdigest()
        pw_db = user["PASS"]
        if pw_hash != pw_db:
            return render_template("election_stand.html", error="Authentication failed")

        if check_query is not None:
            print("DELETING")
            db["CANDIDATES"].find_one_and_delete(
                {"CANDIDATE_ID": str(user["_id"])})
            return render_template("election_stand.html", unlisted="Successfully withdrew")
        else:
            db["CANDIDATES"].insert_one({
                "CANDIDATE_ID": str(user["_id"]),
                "ELECTION_ID": election,
                "REGION": user["VOTE_REGION"],
                "MANIFESTO": request.form.get("manifesto")
            })

            return render_template("election_stand.html", succ="Successfully registered")

    if check_query is not None:
        return render_template("election_stand.html", manifesto=check_query["MANIFESTO"])

    return render_template("election_stand.html")


@app.route('/election/vote', methods=("POST", "GET"))
@jwt_required()
def election_vote():
    username = json.loads(get_jwt_identity())["user"]
    user_id = db["USERS"].find_one({"USR_NAME": username})["_id"]
    form = ElectionsVote(request.form, username)

    candidates = form.candidate.choices

    election_id = str(db["ELECTIONS"].find_one({})["_id"])
    votes_query = db["VOTES"].find_one({
        "VOTER_ID": str(user_id),
        "ELECTION_ID": election_id
    })
    if votes_query is not None:
        print(votes_query)
        return render_template("election_vote.html", info="Already voted in this election", candidates=candidates)

    if form.validate():
        print("Form Validated")

        pw_hash = hashlib.sha256(request.form.get(
            "password").encode()).hexdigest()
        pw_db = db["USERS"].find_one({"USR_NAME": username})["PASS"]
        if pw_hash != pw_db:
            return render_template("election_vote.html", error="Failed authentication")

        user_id = db["USERS"].find_one({"USR_NAME": username})["_id"]
        user_state = db["USERS"].find_one(
            {"USR_NAME": username})["VOTE_REGION"]

        election_id = str(db["ELECTIONS"].find_one({})["_id"])
        votes_query = db["VOTES"].find_one({
            "VOTER_ID": str(user_id),
            "ELECTION_ID": election_id
        })
        if votes_query is not None:
            print(votes_query)
            return Response(status=400)

        db["VOTES"].insert_one({
            "VOTER_ID": str(user_id),
            "CANDIDATE_ID": request.form["candidate"],
            "ELECTION_ID": election_id,
            "STATE": user_state,
            "TIME": datetime.datetime.now()
        })

        return Response(status=200)

    return render_template("election_vote.html", candidates=candidates)


@app.route("/election/results", methods=("POST", "GET"))
def election_results():
    election_latest = db["ELECTIONS"].find_one()
    candidates = db["CANDIDATES"].find({
        "ELECTION_ID": str(election_latest["_id"])
    })

    vote_lst = []
    for candidate in candidates:
        votes = db["VOTES"].count_documents({
            "CANDIDATE_ID": candidate["CANDIDATE_ID"]
        })
        candidate_name = db["USERS"].find_one({
            "_id" : ObjectId(candidate["CANDIDATE_ID"])
        })
        
        vote_lst.append({
            "CANDIDATE_ID" : candidate["CANDIDATE_ID"],
            "VOTES" : votes,
            "NAME" : candidate_name["NAME"],
            "USR_NAME" : candidate_name["USR_NAME"],
            "STATE" : candidate["REGION"]
        })
    return render_template("election_results.html", vote_list=vote_lst)


@app.route("/loan", methods=("GET", "POST"))
@jwt_required()
def loan():
    if request.method == 'GET':
        success = request.args.get('success') or False
        eligible = request.args.get('eligible') or "1"
        eligible = eligible == "1"
        print(eligible)
        return render_template("loan.html", success=success, eligible=eligible)

    user = json.loads(get_jwt_identity())["user"]

    form = LoanForm()
    # if form.validate():
    db["LOANS"].insert_one({
        'USR_NAME': user,
        'APPLICATION_DATE': datetime.datetime.now(),
        'REVIEW_DATE': None,
        'TIME_DURATION': request.form.get('time_duration'),
        'INTEREST': 0.08,
        'AMOUNT': request.form.get('amount'),
        'L_TYPE': request.form.get('l_type'),
        'ASSETS': {
            'housing': request.form.get('assets_housing'),
            'car': request.form.get('assets_car'),
            'gold': request.form.get('assets_gold')
        },
        'CONFIDENCE': 0,
        'APPROVE_STATUS': False,
        'RETURNED': 0,
        'GENDER': request.form.get("gender"),
        "MARRIED": request.form.get("married"),
        "DEPENDENTS": request.form.get("dependents"),
        "EDUCATION": request.form.get("education"),
        "SELF_EMPLOYED": request.form.get("self_employed"),
        "APPLICANTINCOME": request.form.get("applicantincome"),
        "COAPPLICANTINCOME": request.form.get("coapplicantincome"),
        "PROPERTY_AREA": request.form.get("property_area"),
    })

    features = [
        [
            request.form.get("gender") == "male",
            request.form.get("married") == "true",
            request.form.get("dependents") if int(request.form.get(
                "dependents")) < 3 else 3,
            request.form.get("education") == "true",
            request.form.get("self_employed") == "true",
            int(request.form.get("applicantincome"))/80,
            int(request.form.get("coapplicantincome"))/80,
            int(request.form.get("amount"))/80,
            int(request.form.get("time_duration")) * 365,
            request.form.get("property_area") == "urban"
        ]
    ]

    print(features)
    flag = MODEL.predict(features)
    print(flag)

    flag = flag[0] > 0.6

    p = int(request.form.get("amount"))
    n = int(request.form.get("time_duration"))
    r = 0.08

    # ci = int(request.form.get("amount"))*((1+0.08) **
    #                                       (int(request.form.get("time_duration"))))
    # ei = int(request.form.get("applicantincome")) * \
    #     ((1+0.04)**(int(request.form.get("time_duration"))))
    # P x R x (1+R)^N / [(1+R)^N-1]
    ci = (p*r*(1+r)**n)/((1+r)**(n-1))
    ei = int(request.form.get("applicantincome")) - \
        0.1*int(request.form.get("applicantincome"))

    print(ci, ei, flag)
    if ci > ei:
        flag = False
    flag = int(flag)
    return redirect(url_for('loan', success=True, eligible=flag))

@jwt.unauthorized_loader
def unauthorized_jwt_token(message="JWT Auth failed"):
    return render_template('jwt_unauthorized.html')
