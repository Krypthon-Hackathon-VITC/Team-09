from flask_jwt_extended import get_jwt_identity

import hashlib
import json

from app import db


def get_balance_from_username(username: str):
    return db["USERS"].find_one({"USR_NAME" : username})['BALANCE']


def get_hash(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


def check_password_hash(password: str, hash: str):
    if get_hash(password) == hash:
        return True
    return False


def get_jwt_username():
    return json.loads(get_jwt_identity())["user"]


def get_jwt_user_object():
    username = get_jwt_username()
    return db["USERS"].find_one({"USR_NAME": username})
