import os
import joblib
from flask import Flask
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or "super-secret-key"
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY") or "super-secret-jwt-secret-key"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_COOKIE_PATH"] = '/'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
jwt = JWTManager(app)

mongo_uri = os.environ.get("MONGO_URI") or "mongo-uri"
model_path = os.environ.get("MODEL_PATH")

maxSevSelDelay=1000
mongodb = MongoClient(mongo_uri, serverSelectionTimeoutMS=maxSevSelDelay)
db = mongodb['BANK_DATA']

MODEL = joblib.load(model_path)

import endpoints
