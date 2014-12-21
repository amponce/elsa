from flask import Flask, url_for, render_template, flash, request, session, redirect, g
from flask.ext.sqlalchemy import SQLAlchemy
import datetime
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
	try:
		if helpers.validate_form_on_submit(form):
			user = form.get_user()

			check = form.validate_login(user)
			if check:
				login.login_user(user)
				return redirect(url_for('home'))
			else:
				flash('Wrong login/pw!')
				return redirect(url_for('signin'))

	except Exception as e:
		flash('error logging in: ', e)
		return redirect(url_for('index'))


@app.route('/home')
def home():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	resume = db.session.query(models.Resume).filter_by(user_id=login.current_user.id).first()
	active_tests = db.session.query(models.ABTests).filter((models.ABTests.user_id == login.current_user.id) & (models.ABTests.end_date == None)).all()
	completed_tests = db.session.query(models.ABTests).filter((models.ABTests.user_id == login.current_user.id) & (models.ABTests.end_date != None)).all()

	#saving this for admin portal
	role = db.session.query(models.Roles).filter_by(id=login.current_user.role_id).first()
	#user_data = db.session.query(models.User).filter_by(id=login.current_user.id).first()

	# need to only execute this based on role.
	posting_dash = db.engine.execute("select  j.id, j.title, j.created, count(p.id) n from jobs j left outer join pipeline p on p.job_id = j.id where j.poster_id = %s group by 1, 2, 3", login.current_user.id)
	jobs_applied = db.session.query(models.Jobs, models.Pipeline).join(models.Pipeline).filter((models.Pipeline.applicant==login.current_user.id) & (models.Pipeline.status=='applied')).all()

	return render_template('home.html', logged_in=login.current_user.is_authenticated()
						   , resume=resume
						   , tests=active_tests
						   , completed_tests=completed_tests
						   , user_id=login.current_user.id
						   , role=role
						   , postings=posting_dash
						   , jobs_applied=jobs_applied
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

	dash_query = '''    select  r.recipe,
								r.version,
								count(distinct v.id) views,
								count(distinct case when p.status = 'saved' then p.id else null end) saves
						from ab_tests t
						join recipes r
						on r.test_id = t.id
						left outer join views v
						on v.recipe_id = r.id
						left outer join pipeline p
						on p.resume = r.id
						where p.applicant = %s
						and t.id = %s
						group by 1, 2
						'''

	test_data = db.engine.execute(dash_query, (login.current_user.id, test_id))
	return render_template('view_test.html', test_id=test_id
						   , recipes=test_data
						   , test_details=test_data)


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


@app.route('/endTest/<int:test_id>')
def endTest(test_id):
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))
	test = db.session.query(models.ABTests).filter_by(id=test_id).first()
	test.end_date = datetime.datetime.utcnow
	try:
		db.session.add(test)
		db.session.commit()
		flash('Test successfully ended!')
		return redirect(url_for('home'))
	except Exception as e:
		flash('Error ending test: ', e)
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
		flash('error:', e)
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

	if not form.validate_application(form):
		flash('application exists already')
		return redirect(url_for('home'))

	perspective = db.session.query(models.Views).filter((models.Views.recruiter_id==login.current_user.id)&(models.Views.candidate_id==form.applicant.data)).first()
	if perspective:
		#look up the existing view and return it
		recipe = db.session.query(models.Recipes).filter_by(id=perspective.recipe_id).first()
		form.resume.data = recipe.id
	else:
		coin_flip = random.randrange(0, 100)
		control_flag = True if coin_flip < 51 else False
		if control_flag:
			recipe = db.session.query(models.Recipes).filter((models.Recipes.test_id==form.resume.data)&(models.Recipes.recipe=='Control')).first()
			form.resume.data = recipe.id
		else:
			recipe = db.session.query(models.Recipes).filter((models.Recipes.test_id==form.resume.data)&(models.Recipes.recipe<>'Control')).first()
			form.resume.data = recipe.id

	form.populate_obj(add_application)
	try:
		db.session.add(add_application)
		db.session.commit()

		flash('Successfully applied!')
		return redirect(url_for('home'))
	except Exception as e:
		flash('Error applying to job: %s' % e)
		return redirect(url_for('home'))

@app.route('/pipeline/<int:job_id>')
def pipeline_view(job_id):
	#need to add check that the job poster is accessing this page.
	if not login.current_user.is_authenticated() and login.current_user.role_id > 0:
		flash('Not authorized to view this page.')
		return redirect(url_for('home'))

	pipeline = db.session.query(models.User, models.Pipeline).join(models.Pipeline).filter(models.Pipeline.job_id==job_id).all()
	return render_template('pipeline_view.html', pipeline=pipeline)
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
	page_num = request.args.get('page', '')

	if page_num:
		results = search.jobSearch(query, page_num)
	else:
		results = search.jobSearch(query, 1)

	records = len(results)
	pages = records / 10
	return render_template('search.html', job_q=query
						   , results=results
						   , pages=pages
						   , current_page=page_num
						   , query=query)

@app.route('/candidateSearch', methods=['GET'])
def find_candidates():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	query = request.args.get('dude_q', '')
	page_num = request.args.get('page', '')

	if page_num:
		results = search.candidateSearch(query, page_num)
	else:
		results = search.candidateSearch(query, 1)

	#search_results = results if not page_num else results[page_num*10:page_num*10+10]
	records = len(results)
	pages = records / 10
	return render_template('candidate_search.html', results=results
												  , pages=pages
												  , current_page=page_num
												  , query=query)

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
	applied = db.session.query(models.Pipeline).filter((models.Pipeline.applicant==candidate_id)&(models.Pipeline.status=='applied')).first()
	perspective = db.session.query(models.Views).filter((models.Views.recruiter_id==login.current_user.id)&(models.Views.candidate_id==candidate_id)).first()

	if applied.id and not perspective.id:
		view = models.Views(recruiter_id=login.current_user.id, candidate_id=candidate_id, recipe_id=applied.resume)
		active_test = db.session.query(models.ABTests).filter((models.ABTests.user_id==candidate_id) & (models.ABTests.end_date == None)).first()

		if active_test.id:
			recipe = db.session.query(models.Recipes).filter_by(id=view.recipe_id).first()
		else:
			#pull standard resume
			recipe = db.session.query(models.Resume).filter_by(user_id=login.current_user.id).first()

		view = models.Views(recruiter_id=login.current_user.id, candidate_id=candidate_id, recipe_id=recipe.id)
		try:
			db.session.add(view)
			db.session.commit()
			flash('Application saved! (existing)')
		except Exception as e:
			db.session.rollback()
			flash('Error saving application: %s' % e)
	else:
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
					recipe = db.session.query(models.Recipes).filter((models.Recipes.test_id==active_test.id)&(models.Recipes.recipe=='Control')).first()
				else:
					recipe = db.session.query(models.Recipes).filter((models.Recipes.test_id==active_test.id)&(models.Recipes.recipe<>'Control')).first()
			else:
				#pull standard resume
				recipe = db.session.query(models.Resume).filter_by(user_id=login.current_user.id).first()

			#record the view
			view = models.Views(recruiter_id=login.current_user.id, candidate_id=candidate_id, recipe_id=recipe.id)
			db.session.add(view)
			db.session.commit()

	resume = db.session.query(models.Recipes).filter_by(id=recipe.id).first()
	reqs = db.session.query(models.Jobs).filter_by(poster_id=login.current_user.id).all()
	return render_template('candidate_view.html', recipe=recipe
						   						, resume=resume.version
												, reqs=reqs
												, candidate_id=candidate_id)

@app.route('/saveResume', methods=['POST'])
def saveResume():
	if not login.current_user.is_authenticated():
		return redirect(url_for('index'))

	form = eforms.Resume(request.form)
	resume = models.Resume()
	check = form.validate_resume(form)

	if not check:
		updated_resume = db.session.query(models.Resume).filter_by(user_id=login.current_user.id).first()
		updated_resume.resume = form.resume.data

		try:
			db.session.add(updated_resume)
			db.session.commit()
			#need to update the index.
			flash('Resume Updated!')
		except Exception as e:
			flash('Error updating resume: ', e)
		return redirect(url_for('home'))
	else:
		form.populate_obj(resume)

		try:
			db.session.add(resume)
			db.session.commit()
			search.addCandidate(resume.user_id)
			flash('Resume Saved!')
		except Exception as e:
			flash('Error saving Resume: ', e)
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