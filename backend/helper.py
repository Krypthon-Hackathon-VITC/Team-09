from flask_jwt_extended import get_jwt_identity

import hashlib
import json

from app import db

def get_balance(username: str):
    return db["USERS"].find_one({"USR_NAME" : username})['BALANCE']

def check_password_hash(password: str, hash: str):
    if hashlib.sha256(password.encode()).hexdigest() == hash:
        return True
    return False

def get_jwt_user():
    return json.loads(get_jwt_identity())["user"]


def get_jwt_user_object():
    username = get_jwt_user()
    return db["USERS"].find_one({"USR_NAME": username})
