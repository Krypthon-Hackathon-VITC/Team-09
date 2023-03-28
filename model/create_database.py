import pymongo
import time
import datetime
import random
import hashlib
import pickle

import model

print("[ & ] CONNECTION TO MONGO")
MONGO_CONNECTOR = pymongo.MongoClient("mongodb+srv://KUSHAL:KUSHAL@bankingsys.nvomilz.mongodb.net/?retryWrites=true&w=majority")
DATABASE = MONGO_CONNECTOR["BANK_DATA"]

#$$$$$$$$$$#

def CREATE_USERS() :
    global USERS, USERS_CREATED

    # user data as a list of dictionaries
    USERS = []
    # map to ensure no user is repeated
    USERS_CREATED = {}

    # creating 100 users
    for _ in range(100) :
        usr_data = {}

        # generating user id
        uid = "USR_" + str(_)

        if uid in USERS_CREATED :
            continue

        # generating user data
        name = ""
        for _ in range(random.randint(6, 20)) :
            name += "qazwsxedcrfvtgbyhnujmikolp"[random.randint(0, 25)]
        passwd = ""
        for _ in range(random.randint(8, 20)) :
            passwd += "qwertyuiopasdfghjklzxcvbnm"[random.randint(0, 25)]
        phone = ""
        for _ in range(10) :
            phone += "1234567890"[random.randint(0, 9)]
        pan = ""
        for _ in range(20) :
            pan += "9087654321"[random.randint(0, 9)]
        acc_type = ["savings", "savings", "current"][random.randint(0, 2)]
        usr_type = ["regular", "board_member", "board_member"][random.randint(0, 2)]

        # creating dictionary for user data to add to USERS_CREATED
        usr_data["USR_NAME"] = uid
        usr_data["NAME"] = name
        usr_data["PASS"] = passwd ## CHEK FOR HASH ALGO
        usr_data["PHONE"] = phone
        usr_data["PAN"] = pan
        usr_data["ACC_TYPE"] = acc_type
        usr_data["USR_TYPE"] = usr_type
        usr_data["BALANCE"] = random.randint(1000000, 10000000)

        # storing hash of password
        usr_data["PASS"] = hashlib.sha256(bytes(usr_data["PASS"], "utf-8")).hexdigest()

        # storing user data
        USERS_CREATED[uid] = uid
        USERS.append(usr_data)

#$$$$$$$$$$#

def CREATE_TRANSACTIONS() :
    global USERS
    global USERS_CREATED
    global TRANSACTIONS

    # creating virtual/augmented transactions
    TRANSACTIONS = []
    # map to ensure no transation has more than 1 entry
    TRANSACTIONS_MADE = {}

    # creating 100000 transactions
    for _ in range(100000) :
        transaction = {}
        # time of transaction event
        time = datetime.datetime(2022,
                                 random.randint(1, 12),
                                 random.randint(1, 28),
                                 random.randint(0, 23),
                                 random.randint(0, 59),
                                 random.randint(0, 59))
        # from user to to user transaction has been done
        usrs = list(USERS_CREATED.keys())
        from_ = usrs[random.randint(0, len(usrs) - 1)]
        to = usrs[random.randint(0, len(usrs) - 1)]

        # if from is to then continue as cant send money to self
        if from_ == to :
            continue

        # random amount sent
        amount = random.randint(1000, 10000)
        # random remark
        remark = ""
        for _ in range(random.randint(20, 100)) :
            remark += "qazw sxe dcr fvt gby hnu jmi kol p12 345 678 90"[random.randint(0, 46)]
        
        transaction["TIME"] = time
        transaction["FROM"] = from_
        transaction["TO"] = to
        transaction["AMOUNT"] = amount
        transaction["REMARK"] = remark

        # save transaction
        TRANSACTIONS.append(transaction)

#$$$$$$$$$$#

def CREATE_LOANS() :
    global USERS
    global USERS_CREATED
    global LOANS_REQUESTED 

    # creating virtualised/augmented loan requests
    LOANS_REQUESTED = []
    # map to ensure no loan req is duplicated or have double entry with different data
    LOANS = {}

    # creating 10000 loan requests
    for _ in range(10000) :
        # seed random value to remove evenness from data
        random.seed(time.time() - random.choice([x**3 for x in range(-15, 15)]))
        loan = {}
        # loan id
        lid = str(random.randint((10**50) + 1, (10**51) - 1))
        # preventing repetation of loan entries with different data and same id
        if lid in LOANS :
            continue
        usrs = list(USERS_CREATED.keys())
        uid = usrs[random.randint(0, len(usrs) - 1)]
        # loan application date
        app_date = [2022,
                    random.randint(1, 12),
                    random.randint(1, 23),
                    random.randint(0, 23),
                    random.randint(0, 59),
                    random.randint(0, 59)]
        # loan review date
        review_time = [2022,
                       app_date[1],
                       app_date[2] + random.randint(1, 5),
                       random.randint(0, 23),
                       random.randint(0, 59),
                       random.randint(0, 59)]

        app_date_ = datetime.datetime(*app_date)
        review_date_ = datetime.datetime(*review_time)
        time_duration = random.randint(1, 5)
        interest = round(random.randint(3, 15)/100, 2)
        amount = random.randint(10000, 10000000)
        l_type = ["housing", "education", "car",
                  "gold", "personal", "business"][random.randint(0, 5)]
        assets = {}
        for _ in ["housing", "car", "gold"] :
            temp = random.randint(0, 1)
            if temp :
                cost = random.randint(10000, 10000000)
                assets[_] = cost
        confidence = random.randint(1, 100)
        approve_status = False
        if confidence > 60 :
            approve_status = True
        loan_returned = False
        if approve_status :
            loan_returned = [True, False][random.randint(0, 1)]

        # creating dictionary
        loan["LID"] = lid
        loan["UID"] = uid
        loan["APPLICATION_DATE"] = app_date_
        loan["REVIEW_DATE"] = review_date_
        loan["TIME_DURATION"] = time_duration
        loan["INTEREST"] = interest
        loan["AMOUNT"] = amount
        loan["L_TYPE"] = l_type
        loan["ASSETS"] = assets
        loan["CONFIDENCE"] = confidence
        loan["APPROVE_STATUS"] = approve_status
        loan["RETURNED"] = loan_returned

        # saving loans
        LOANS[lid] = lid
        LOANS_REQUESTED.append(loan)

def UPLOAD_DB_SERVER() :
    global DATABASE
    global USERS
    global TRANSACTIONS
    global LOANS_REQUESTED

    # connecting to clooections and resetting them
    USER_COLLECTION = DATABASE["USERS"]
    USER_COLLECTION.drop()
    TRANSACTION_COLLECTION = DATABASE["TRANSACTIONS"]
    TRANSACTION_COLLECTION.drop()
    LOANS_COLLECTION = DATABASE["LOANS"]
    LOANS_COLLECTION.drop()

    # uploading the data generated to atlas server
    USER_COLLECTION.insert_many(USERS)
    TRANSACTION_COLLECTION.insert_many(TRANSACTIONS)
    LOANS_COLLECTION.insert_many(LOANS_REQUESTED)

def TRAIN_MODELS() :
    global FEATURES
    global TARGETS
    global LOANS_REQUESTED
    # creating features and targets for models
    FEATURES = []
    TARGETS = []

    # adding all the features for model
    # amount, time duration, interest, assets
    # confidence is the target
    for _ in range(len(LOANS_REQUESTED)) :
        FEATURES.append([])
        FEATURES[-1].append(LOANS_REQUESTED[_]["AMOUNT"])
        FEATURES[-1].append(LOANS_REQUESTED[_]["TIME_DURATION"])
        FEATURES[-1].append(LOANS_REQUESTED[_]["INTEREST"])
        asset_sum = 0
        for __ in LOANS_REQUESTED[_]["ASSETS"] :
            asset_sum += LOANS_REQUESTED[_]["ASSETS"][__]
        FEATURES[-1].append(asset_sum)
        FEATURES[-1].append(random.randint(0, 1000000))
        #if LOANS_REQUESTED[_]["CONFIDENCE"] > 0.7

        TARGETS.append(LOANS_REQUESTED[_]["CONFIDENCE"])

    # create model object
    MODEL = model.HOUSE_PRICE_PREDICTOR()
    # train
    MODEL.train(FEATURES, TARGETS)
    # print accuracy
    print("[ % ] SCORE IS", MODEL.score(FEATURES, TARGETS))

    # open a file and save the pickle of model
    MODEL_FILE = open("MODEL.pkl", "wb")
    pickle.dump(MODEL, MODEL_FILE)

if __name__ == "__main__" :
    print("[ # ] CREATING USERS")
    CREATE_USERS()
    print("[ ~ ] CREATING TRANSACTIONS")
    CREATE_TRANSACTIONS()
    print("[ $ ] CREATING LOANS")
    CREATE_LOANS()

    # UNCOMMENT THESE LINES TO RESET ATLAS DB
    #
    #print("[ ^ ] UPLOADING")
    #UPLOAD_DB_SERVER()
    #BANK_FUNDS = DATABASE["FUNDS"]
    #BANK_FUNDS.insert_one({"FUNDS": 100000000000000,
    #                       "CREDIT": 123123123123,
    #                       "DEBIT": 456475675876})

    print("[ * ] TRAINING MODEL")
    TRAIN_MODELS()
