from app import db

def get_balance(username: str):
    return db["USERS"].find_one({"USR_NAME" : username})['BALANCE']
    
