from bson import ObjectId
from flask import jsonify, render_template, Response, request, \
    make_response, url_for, redirect
from flask_jwt_extended import create_access_token, get_jwt_identity, \
    jwt_required, set_access_cookies, get_jwt
from helper import *
from collections import defaultdict
import pprint
pp = pprint.PrettyPrinter(indent=1)

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
        target_timestamp = datetime.datetime.timestamp(
            now + datetime.timedelta(minutes=15))
        if target_timestamp - exp_timestamp < 15:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response

@app.route("/delete_token", methods=("GET",))
@jwt_required()
def delete_token():
    resp = make_response(redirect(url_for("homepage")))
    token = create_access_token(identity=get_jwt_identity(), expires_delta=datetime.timedelta(days=-1000))
    set_access_cookies(resp, token)
    return resp

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
    form = ComplaintForm(request.form)
    username = get_jwt_username()
    if form.validate():
        subject = form["subject"].data
        body = form["body"].data
        db["TICKETS"].insert_one({
            "FROM": username,
            "SUBJECT": subject,
            "BODY": body,
            "TIME": datetime.datetime.now(),
            "STATUS": False,
            "TICKET_ID": str(uuid.uuid4()).replace("-", ""),
            "REPLY": ""
        })
        return render_template('complaint.html', success="Ticket successfully created!")

    tickets = list(db["TICKETS"].find({'FROM': username}))
    return render_template("complaint.html", tickets=tickets)


@app.route("/signup", methods=("POST",))
def signup():
    form = SignupForm(request.form)

    if form.validate():
        username = form["username"].data
        name = form["name"].data
        phone = form["phone"].data
        password = form["password"].data
        confirm_password = form["confirm_password"].data
        pan = form["pan"].data
        pincode = form["pin"].data
        account_type = form["account_type"].data

        query = db["USERS"].find_one({"USR_NAME": username})
        if query is not None:
            return Response(status=400)

        if password != confirm_password:
            return Response(status=400)

        pin_query = db["PINCODE"].find_one({"Pincode": pincode})
        if pin_query is None:
            return Response(status=410)
        vote_region = pin_query["StateName"]

        db["USERS"].insert_one({
            'USR_NAME': username,
            'NAME': name,
            'PASS': get_hash(password),
            'PHONE': phone,
            'PAN': pan,
            'PIN': pincode,
            'VOTE_REGION': vote_region,
            'ACC_TYPE': account_type,
            'USR_TYPE': "regular",
            'BALANCE': 0,
        })

        return Response(status=200)
    return Response(status=411)


@app.route("/election/board", methods=("GET",))
@jwt_required()
def election_board():
    members = db['USERS'].find({"USR_TYPE": "board_member"})
    return render_template("election_board.html", members=members)


@app.route("/election/candidates", methods=("GET",))
@jwt_required()
def election_candidates():
    election_latest = db["ELECTIONS"].find_one()
    candidates = list(db["CANDIDATES"].find({
        "ELECTION_ID": str(election_latest["_id"])
    }))
    regions = set()
    for i in range(len(candidates)):
        candidate_info = db["USERS"].find_one({
            "_id" : ObjectId(candidates[i]["CANDIDATE_ID"])
        })
        candidates[i]['CANDIDATE_INFO'] = candidate_info
        regions.add(candidates[i]['REGION'])

    regions = list(regions)
    candidates_by_region = defaultdict(list)
    for region in regions:
        candidates_by_region[region].extend(filter(lambda x: x['REGION'] == region, candidates))

    return render_template("election_candidates.html", cbr=candidates_by_region)

@app.route("/election/stand", methods=("POST", "GET"))
@jwt_required()
def election_stand():
    form = ElectionStand(request.form)
    user = get_jwt_user_object()
    election_id = db["ELECTIONS"].find_one()["_id"]

    check_query = db["CANDIDATES"].find_one({
        "CANDIDATE_ID": user["_id"],
        "ELECTION_ID": election_id
    })
    if form.validate():
        manifesto = form["manifesto"].data
        password = form["password"].data

        if not verify_password_jwt(password):
            print("Pass fail")
            return render_template("election_stand.html",
                                   error="Authentication failed")

        if check_query is not None:
            db["CANDIDATES"].find_one_and_delete(
                {"CANDIDATE_ID": user["_id"]})
            return render_template("election_stand.html", 
                                   unlisted="Successfully withdrew")
        else:
            db["CANDIDATES"].insert_one({
                "CANDIDATE_ID": user["_id"],
                "ELECTION_ID": election_id,
                "REGION": user["VOTE_REGION"],
                "MANIFESTO": manifesto
            })

            return render_template("election_stand.html",
                                   success="Successfully registered")

    if check_query is not None:
        manifesto = check_query["MANIFESTO"]
        return render_template("election_stand.html", manifesto=manifesto)

    return render_template("election_stand.html")


@app.route('/election/vote', methods=("POST", "GET"))
@jwt_required()
def election_vote():
    username = get_jwt_username()
    form = ElectionsVote(request.form, username)

    user = get_jwt_user_object()
    candidates = form.candidate.choices
    election_id = db["ELECTIONS"].find_one()["_id"]

    votes_query = db["VOTES"].find_one({
        "VOTER_ID": user["_id"],
        "ELECTION_ID": election_id
    })
    if votes_query is not None:
        return render_template("election_vote.html",
                               info="Already voted in this election",
                               candidates=candidates)

    if form.validate():
        candidate = form["candidate"].data
        password = form["password"].data
        if not verify_password_jwt(password):
            return render_template("election_vote.html",
                                   error="Failed authentication")

        user_id = user["_id"]
        user_state = user["VOTE_REGION"]

        db["VOTES"].insert_one({
            "VOTER_ID": user_id,
            "CANDIDATE_ID": ObjectId(candidate),
            "ELECTION_ID": election_id,
            "STATE": user_state,
            "TIME": datetime.datetime.now()
        })

        return render_template("election_vote.html", candidates=candidates, 
                               success="Successfully voted!")

    return render_template("election_vote.html", candidates=candidates)


@app.route("/election/results", methods=("POST", "GET"))
def election_results():
    election = db["ELECTIONS"].find_one()
    candidates = db["CANDIDATES"].find({
        "ELECTION_ID": election["_id"]
    })

    votes_list = []
    for candidate in candidates:
        votes = db["VOTES"].count_documents({
            "CANDIDATE_ID": candidate["CANDIDATE_ID"]
        })
        candidate_name = db["USERS"].find_one({
            "_id" : ObjectId(candidate["CANDIDATE_ID"])
        })
        
        votes_list.append({
            "CANDIDATE_ID" : candidate["CANDIDATE_ID"],
            "VOTES" : votes,
            "NAME" : candidate_name["NAME"],
            "USR_NAME" : candidate_name["USR_NAME"],
            "STATE" : candidate["REGION"]
        })
    return render_template("election_results.html", vote_list=votes_list)


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
