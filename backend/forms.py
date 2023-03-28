from wtforms import Form, StringField, PasswordField, SubmitField, SelectField, ValidationError, IntegerField, RadioField
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


class TransferForm(Form):
    user_to = StringField('user_to', validators=[input_required()])
    amount = IntegerField('amount', validators=[input_required()])
    remark = StringField('remark')
    submit = SubmitField('submit')

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


class LoanForm(Form):
    time_duration = IntegerField("time_duration", validators=[input_required()])
    amount = IntegerField("time_duration", validators=[input_required()])
    l_type = SelectField("l_type", choices=[
        ("home", "Home Loan"),
        ("business", "Business Loan"),
        ("car", "Car Loan"),
        ("personal", "Personal Loan")
    ], validators=[input_required()])
    assets_housing = IntegerField("assets_housing", validators=[input_required()])
    assets_car = IntegerField("assets_car", validators=[input_required()])
    assets_gold = IntegerField("assets_gold", validators=[input_required()])
    gender = RadioField('gender', choices=[
        ("male", "Male"),
        ("female", "Female")
    ], validators=[input_required()])
    married = RadioField('married', choices=[
        ("true", "Married"),
        ("false", "Unmarried")
    ], validators=[input_required()])

    education = RadioField('education', choices=[
        ("true", "Graduate"),
        ("false", "Not a Graduate")
    ], validators=[input_required()])

    self_employed = RadioField('self_employed', choices=[
        ("true", "Self Employed"),
        ("false", "Not Self Employed")
    ], validators=[input_required()])

    property_area = RadioField('property_area', choices=[
        ("urban", "Urban"),
        ("rural", "Rural")
    ], validators=[input_required()])

    dependents = IntegerField("dependents", validators=[input_required()])
    applicantincome = IntegerField("applicantincome", validators=[input_required()])
    coapplicantincome = IntegerField("coapplicantincome", validators=[input_required()])
