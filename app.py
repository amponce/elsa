from flask import Flask, url_for, render_template, flash, request, session, redirect, g
from flask.ext.sqlalchemy import SQLAlchemy

from flask.ext import admin, login
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import form, fields, validators
from flask.ext.admin.contrib import sqla
from flask.ext.admin import helpers, expose
from sqlalchemy import and_
import os
import random

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config.debug = True
db = SQLAlchemy(app)

# custom app classes
import models
import search
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
	role = db.session.query(models.Roles).filter_by(id=login.current_user.role_id).first()

	postings = db.session.query(models.Jobs).filter_by(poster_id=login.current_user.id)

	return render_template('home.html', logged_in=login.current_user.is_authenticated()
						   , resume=resume
						   , tests=tests
						   , user_id=login.current_user.id
						   , role=role
						   , postings=postings
						   , username=login.current_user.email)


# --------------------------------------------------------------------
#
# Begin Testing Block
#
# --------------------------------------------------------------------
@app.route('/viewTest/<int:test_id>')
def viewTest(test_id):
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	recipes = db.session.query(models.Recipes).filter_by(test_id=test_id)
	test_details = db.session.query(models.ABTests).filter_by(id=test_id).first()

	return render_template('view_test.html', test_id=test_id
						   , recipes=recipes
						   , test_details=test_details)


@app.route('/addTest', methods=['POST'])
def addTest():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	form = eforms.testForm(request.form)
	tests = models.ABTests()
	form.populate_obj(tests)

	resume = db.session.query(models.Resume).filter_by(user_id=login.current_user.id).first()

	try:
		db.session.add(tests)
		db.session.commit()
		flash('test saved')
		return render_template('recipes.html', test_id=tests.id
							   , user_id=login.current_user.id
							   , resume=resume)
	except Exception as e:
		flash('error: ', e)
		return redirect(url_for('home'))


@app.route('/addRecipe', methods=['POST'])
def addRecipe():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	test_id = request.form['test_id']
	recipes = request.form.getlist('recipe')
	versions = request.form.getlist('version')

	try:
		for i, value in enumerate(recipes):
			recipe = models.Recipes(test_id=test_id, recipe=value, version=versions[i])
			db.session.add(recipe)
			db.session.commit()

		flash('Successfully added recipes!')
		return render_template(url_for('home'))

	except Exception as e:
		flash('error: %s' % e)
		return redirect(url_for('home'))


#--------------------------------------------------------------------
#
#						End Testing Block
#
#--------------------------------------------------------------------

#--------------------------------------------------------------------
#
#						Begin Job Posting Block
#
#--------------------------------------------------------------------
@app.route('/newJob')
def newJob():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	return render_template('job_posting.html', user_id=login.current_user.id)


@app.route('/addJob', methods=['POST'])
def addJob():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	form = eforms.jobsForm(request.form)
	job = models.Jobs()
	form.populate_obj(job)

	try:
		db.session.add(job)
		db.session.commit()
		search.addJob(job.id)
		flash('Successfully added job!')
		return redirect(url_for('home'))
	except Exception as e:
		flash('Error posting job: %s' % e)
		return redirect(url_for('home'))

@app.route('/viewJob/<int:job_id>')
def viewJob(job_id):
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))
	job_details = db.session.query(models.Jobs).filter_by(id=job_id).first()
	tests = db.session.query(models.ABTests).filter_by(user_id=login.current_user.id).all()
	return render_template('view_job.html', details=job_details
						   , tests=tests
						   , applicant=login.current_user.id)


@app.route('/apply', methods=['POST'])
def apply():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	form = eforms.Pipeline(request.form)
	add_application = models.Pipeline()
	form.populate_obj(add_application)

	if not form.validate_application(form):
		flash('application exists already')
		return redirect(url_for('home'))

	try:
		db.session.add(add_application)
		db.session.commit()

		flash('Successfully applied!')
		return redirect(url_for('home'))
	except Exception as e:
		flash('Error applying to job: %s' % e)
		return redirect(url_for('home'))

#--------------------------------------------------------------------
#
#						End Job Posting Block
#
#--------------------------------------------------------------------

#--------------------------------------------------------------------
#
#						Begin Search Block
#
#--------------------------------------------------------------------
@app.route('/jobSearch', methods=['GET'])
def jobSearch():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	query = request.args.get('job_q', '')
	results = search.jobSearch(query)
	return render_template('search.html', job_q=query
						   , results=results)

@app.route('/candidateSearch', methods=['GET'])
def find_candidates():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	query = request.args.get('dude_q', '')
	results = search.candidateSearch(query)
	return render_template('candidate_search.html', results=results)

#--------------------------------------------------------------------
#
#						End Search Block
#
#--------------------------------------------------------------------

@app.route('/viewCandidate/<int:candidate_id>')
def view_candidate(candidate_id):
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	recruiter_id = login.current_user.id

	#first check to see if this person applied, and see if
	#a test was selected, then apply that view.

	#see if the recruiter has viewed this profile before:
	perspective = db.session.query(models.Views).filter((models.Views.recruiter_id==login.current_user.id)&(models.Views.candidate_id==candidate_id)).first()
	if perspective:
		#look up the existing view and return it
		recipe = db.session.query(models.Recipes).filter_by(id=perspective.recipe_id).first()
	else:
		#get a view to return
		active_test = db.session.query(models.ABTests).filter((models.ABTests.user_id==candidate_id) & (models.ABTests.end_date == None)).first()
		if active_test:
			coin_flip = random.randrange(0, 100)
			control_flag = True if coin_flip < 51 else False
			if control_flag:
				recipe = db.session.query(models.Recipes).filter((models.Recipes.test_id==22)&(models.Recipes.recipe=='Control')).first()
			else:
				recipe = db.session.query(models.Recipes).filter((models.Recipes.test_id==22)&(models.Recipes.recipe<>'Control')).first()
		else:
			#pull standard resume
			recipe = db.session.query(models.Resume).filter_by(user_id=login.current_user.id).first()

		#record the view
		view = models.Views(recruiter_id=login.current_user.id, candidate_id=candidate_id, recipe_id=recipe.id)
		db.session.add(view)
		db.session.commit()
	return render_template('candidate_view.html', recipe=recipe)

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
		search.addCandidate(resume.user_id)
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