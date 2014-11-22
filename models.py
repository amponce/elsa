from app import db
import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    password = db.Column(db.String(900))


    def __init__(self, email, created):
        self.email = email
        self.created = created

    def __repr__(self):
        return '<id %r>' % self.id