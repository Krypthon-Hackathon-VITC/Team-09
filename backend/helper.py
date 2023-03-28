import hashlib

from app import db

def get_balance(username: str):
    return db["USERS"].find_one({"USR_NAME" : username})['BALANCE']

def check_password_hash(password: str, hash: str):
    if hashlib.sha256(password.encode()).hexdigest() == hash:
        return True
    return False
