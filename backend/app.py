import os
from flask import Flask
from flask_jwt_extended import JWTManager
from pymongo import MongoClient

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
jwt = JWTManager(app)

maxSevSelDelay=1000
try:
    mongodb = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=maxSevSelDelay)
    db = mongodb['BANK_DATA']
except:
    exit(1)