from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import form, fields, validators
from flask.ext import admin, login
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
            return False

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
        if db.session.query(models.User).filter_by(email=self.email.data).count() > 0:
            return validators.ValidationError('Duplicate username')
        else:
            return True

class Resume(form.Form):
    user_id = fields.IntegerField()
    resume = fields.StringField()

    def validate_resume(self, field):
        if db.session.query(models.Resume).filter_by(user_id=self.user_id.data).count() > 0:
            return False
        else:
            return True

class testForm(form.Form):
    user_id = fields.IntegerField()
    test_name = fields.TextField()
    hypothesis = fields.TextField()
    start_date = fields.DateField()
    end_date = fields.DateField()

class recipeForm(form.Form):
    test_id = fields.IntegerField()
    recipe = fields.FieldList(fields.StringField())
    version = fields.FieldList(fields.StringField())

class jobsForm(form.Form):
    poster_id = fields.IntegerField()
    title = fields.StringField()
    description = fields.StringField()
    skills = fields.StringField()
    url = fields.StringField()

class Pipeline(form.Form):
    job_id = fields.IntegerField()
    applicant = fields.IntegerField()
    resume = fields.IntegerField()
    status = fields.StringField()

    def validate_application(self, field):
        if db.session.query(models.Pipeline).filter((models.Pipeline.resume==self.resume.data) & (models.Pipeline.job_id==self.job_id.data)).count() > 0:
            return False
        else:
            return True