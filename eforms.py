from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import form, fields, validators
from app import db
import models

class LoginForm(form.Form):
    email = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            return validators.ValidationError('Invalid user')

        # we're comparing the plaintext pw with the the hash from the db
        if not check_password_hash(user.password, self.password.data):
        # to compare plain text passwords use
        # if user.password != self.password.data:
            return validators.ValidationError('Invalid password')

        return True

    def get_user(self):
        return db.session.query(models.User).filter_by(email=self.email.data).first()

class RegistrationForm(form.Form):
    name = fields.TextField(validators=[validators.required()])
    email = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])
    tagline = fields.TextField(validators=[validators.required()])
    summary = fields.TextField(validators=[validators.required()])

    def validate_login(self, field):
        if db.session.query(User).filter_by(login=self.email.data).count() > 0:
            raise validators.ValidationError('Duplicate username')