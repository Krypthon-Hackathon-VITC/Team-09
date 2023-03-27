import os
from flask import Flask
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or "super-secret-key"
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY") or "super-secret-jwt-secret-key"
jwt = JWTManager(app)

mongo_uri = os.environ.get("MONGO_URI") or "mongo-uri"

maxSevSelDelay=1000
mongodb = MongoClient(mongo_uri, serverSelectionTimeoutMS=maxSevSelDelay)
db = mongodb['BANK_DATA']

import endpoints