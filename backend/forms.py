from wtforms import Form, StringField, PasswordField, SubmitField
from wtforms.validators import input_required

class LoginForm(Form):
    username = StringField('username', validators=[input_required()])
    password = PasswordField('password', validators=[input_required()])
    submit = SubmitField('submit')