from wtforms import Form, StringField, PasswordField, SubmitField, SelectField, ValidationError
from wtforms.validators import input_required, length

import re
from bson.objectid import ObjectId

from app import db

class LoginForm(Form):
    username = StringField('username', validators=[input_required()])
    password = PasswordField('password', validators=[input_required()])
    submit = SubmitField('submit')

class SignupForm(Form):
    username = StringField('username', validators=[input_required()])
    name = StringField('name', validators=[input_required()])
    password = PasswordField('password', validators=[input_required()])
    confirm_password = PasswordField('confirm_password', validators=[input_required()])
    phone = StringField('phone', validators=[input_required(), length(10)])
    pan = StringField('pan', validators=[input_required(), length(10)])
    pin = StringField('pin', validators=[input_required(), length(6)])
    account_type = SelectField('account_type', choices=[
        ('savings', "Savings"),
        ('current', 'Current')
    ], validators=[input_required()])
    submit = SubmitField('submit')

    def validate_account_type(form, field):
        if field.data not in ("savings", "current"):
            raise ValidationError("Invaild Account type")

    def validate_pan(form, field):
        pattern = r"[A-Z]{5}[0-9]{4}[A-Z]{1}"
        if not re.match(pattern, field.data):
            raise ValidationError("Invalid PAN")
            
    def validate_password(form, field):
        pattern = r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"
        if not re.search(pattern, field.data):
            raise ValidationError("Create a strong password >:(")

    def validate_phone(form, field):
        pattern = r"[0-9]{10}"
        if not re.match(pattern, field.data):
            raise ValidationError("Invalid phone number")


class ComplaintForm(Form):
    subject = StringField('subject', validators=[input_required()])
    body = PasswordField('body', validators=[input_required()])
    submit = SubmitField('submit')

class ElectionStand(Form):
    manifesto = StringField('manifesto', validators=[input_required()])
    password = PasswordField('password', validators=[input_required()])
    stand = SubmitField('submit')

class ElectionsVote(Form):
    candidate = SelectField('candidate', validators=[input_required()])
    password = PasswordField('password', validators=[input_required()])
    vote = SubmitField('vote')

    def __init__(self, formdata, username):
        super(ElectionsVote, self).__init__(formdata)   
        choices = []
        user_voting_region = db["USERS"].find_one({"USR_NAME": username})["VOTE_REGION"]
        candidates = db["CANDIDATES"].find({
            "REGION": user_voting_region
        })
        for candidate in candidates:
            cid = candidate["CANDIDATE_ID"]
            cname = db["USERS"].find_one({"_id": ObjectId(cid)})["NAME"]
            choices.append((str(cid), cname))
        self.candidate.choices = choices

class LoanFormPredict(Form):
    gender = StringField('gender', validators=[input_required()])

    