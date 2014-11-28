from flask import Flask, url_for, render_template, flash, request, session, redirect, g
from flask.ext.sqlalchemy import SQLAlchemy

from flask.ext import admin, login
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import form, fields, validators
from flask.ext.admin.contrib import sqla
from flask.ext.admin import helpers, expose
from sqlalchemy import and_
import os
import indeed

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config.debug = True
db = SQLAlchemy(app)

# custom app classes
import models
import eforms


def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(models.User).get(user_id)

# Initialize flask-login
init_login()


@app.route('/')
def index():
	return render_template('index.html')


@app.route('/signin')
def signin():
	return render_template('signin.html')


@app.route('/signup')
def signup():
	return render_template('newaccount.html')


@app.route('/login', methods=['POST'])
def log_in():
	form = eforms.LoginForm(request.form)
	if helpers.validate_form_on_submit(form):
		user = form.get_user()

		check = form.validate_login(user)
		if check:
			login.login_user(user)
			return redirect(url_for('home'))
	else:
		flash('error logging in')
		return redirect(url_for('index'))


@app.route('/home')
def home():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	resume = db.session.query(models.Resume).filter_by(user_id=login.current_user.id).first()
	tests = db.session.query(models.ABTests).filter_by(user_id=login.current_user.id)

	return render_template('home.html', logged_in=login.current_user.is_authenticated()
						   , resume=resume
						   , tests=tests
						   , user_id=login.current_user.id)


@app.route('/addTest', methods=['POST'])
def addTest():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	form = eforms.testForm(request.form)

	return 'addtest'


@app.route('/saveResume', methods=['POST'])
def saveResume():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	form = eforms.Resume(request.form)
	resume = models.Resume()
	form.populate_obj(resume)

	if form.validate_resume(form) == True:
		db.session.add(resume)
		db.session.commit()

		flash('resume saved')
	else:
		flash('resume exists')
	return redirect(url_for('home'))


@app.route('/register', methods=['POST'])
def register():
	form = eforms.RegistrationForm(request.form)
	if helpers.validate_form_on_submit(form):
		user = models.User()
		if form.validate_login(user):
			form.populate_obj(user)

			user.password = generate_password_hash(form.password.data)

			db.session.add(user)
			db.session.commit()

			login.login_user(user)
			flash('logged in!')

			return redirect(url_for('home'))
	else:
		flash('user exists.')
		return redirect(url_for('signup'))

	flash(form.name.data)
	return render_template('debug.html', msg='error')


@app.route('/logout')
def logout():
    login.logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()