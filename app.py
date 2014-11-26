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

#custom app classes
import models
import eforms

def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(User).get(user_id)

@app.route('/')
def index():
	return render_template('index.html') 

# Initialize flask-login
init_login()


@app.route('/signup')
def signup():
	return render_template('newaccount.html')

@app.route('/home')
def home():
	return 'home'

@app.route('/register', methods=['POST'])
def register():
	form = eforms.RegistrationForm(request.form)
	if helpers.validate_form_on_submit(form):
		user = models.User()
		form.populate_obj(user)

		user.password = generate_password_hash(form.password.data)

		db.session.add(user)
		db.session.commit()

		login.login_user(user)
		flash('logged in!')

		return redirect(url_for('home'))
	flash(form.name.data)
	return render_template('debug.html', msg='error')

@app.route('/one', methods=['GET'])
def getStarted():
	email = request.args.get('email')
	first_search = request.args.get('first_search')
	screen = 1

	#update this to write to the paging metadata table
	paging = request.args.get('paging')
	if not paging:
		paging = 0

	data = indeed.getTree(first_search, paging*5)
	results = indeed.getResults(data)

	user = models.User
	skill = models.Skills
	db = models.db
	page = models.Pages

	#next try to add the visitor to get an email
	visitor = user.query.filter_by(email=email).first()
	if visitor is None:
		try:
			visitor = user(email=email, created=None)
			db.session.add(visitor)
			db.session.commit()
		except Exception as e:
			db.session.rollback()

	first_page = page.query.filter(page.user_id==visitor.id).filter(page.screen==1).first()
	try:
		first_page = page(user_id=visitor.id, screen=screen, page=1, created=None, modified=None)
		db.session.add(first_page)
		db.session.commit()
	except Exception as e:
		db.session.rollback()
	
	#finally, add the skill
	first_skill = skill.query.filter(skill.user_id==visitor.id).filter(skill.skill_num==1).first()
	if first_skill is None:
		try:
			first_skill = skill(user_id=visitor.id, skill=first_search, skill_num=1, created=None)
			db.session.add(first_skill)
			db.session.commit()
		except Exception as e:
			db.session.rollback()
	else:
		first_skill.skill = first_search
		db.session.commit()


	return render_template('joblist.html', first_search=first_search,
										   results=results,
										   email=email,
										   skill_check=0,
										   visitor_id=visitor.id,
										   screen=screen)


if __name__ == '__main__':
    app.run()