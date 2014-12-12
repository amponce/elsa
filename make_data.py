from faker import Factory
from app import db
import models
from werkzeug.security import generate_password_hash

fake = Factory.create()

def create_users(n):
    s = 0
    e = 0
    for x in range(0, n):
        user = models.User()
        user.email = fake.email()
        user.password = generate_password_hash('changeme')
        user.tagline = fake.text(100)
        user.summary = fake.text(300)
        user.name = fake.name()

        try:
            db.session.add(user)
            db.session.commit()
            s += 1
        except Exception as e:
            e += 1
            db.session.rollback()
    msg = str(s) + ' user records created, ' + str(e) + ' errors.'
    return msg

