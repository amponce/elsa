from app import db
import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    password = db.Column(db.String(1000))
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    tagline = db.Column(db.String(255))
    summary = db.Column(db.String(4000))
    role_id = db.Column(db.Integer, default=0)

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.email

    def __repr__(self):
        return '<id %r>' % self.id

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    resume = db.Column(db.String(4000))
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<id %r>' % self.id

class ABTests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    test_name = db.Column(db.String(4000))
    hypothesis = db.Column(db.String(4000))
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

    def __repr__(self):
        return '<id %r>' % self.id

class Recipes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer)
    recipe = db.Column(db.String(255))
    version = db.Column(db.String(4000))

    def __repr__(self):
        return '<id %r>' % self.id

class RecipeStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer)
    views = db.Column(db.Integer)
    adds = db.Column(db.Integer)
    latest_activity = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<id %r>' % self.id

class Roles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(255))
    company_id = db.Column(db.Integer)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_recruiter = db.Column(db.Integer)

    def __repr__(self):
        return '<id %r>' % self.id

class Jobs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(4000))
    skills = db.Column(db.String(4000))
    poster_id = db.Column(db.Integer)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires = db.Column(db.DateTime)
    url = db.Column(db.String(4000))

    def __repr__(self):
        return '<id %r>' % self.id

class Pipeline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))
    applicant = db.Column(db.Integer, db.ForeignKey('user.id'))
    resume = db.Column(db.Integer)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(255))

    def __repr__(self):
        return '<id %r>' % self.id

class Views(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    candidate_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<id %r>' % self.id