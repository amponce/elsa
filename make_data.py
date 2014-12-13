from faker import Factory
from app import db
import models
from werkzeug.security import generate_password_hash
import random

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

        user.role_id = 1 if random.randrange(0, 100) > 90 else 0

        try:
            db.session.add(user)
            db.session.commit()

            resume = generateResume(user.id)
            test_id = makeABTest(user.id)

            makeRecipes(test_id, resume)

            if user.role_id == 1:
                makeJobPosting(user.id)

            s += 1
        except Exception as e:
            e += 1
            db.session.rollback()
    msg = str(s) + ' user records created, ' + str(e) + ' errors.'
    return msg

#presuming there's more than 15 records existing
def generateResume(user_id):
    text = fake.text(300) + '\n' + fake.text(300) + '\n' + fake.text(300)
    resume = models.Resume()
    resume.user_id = user_id
    resume.resume = text

    try:
        db.session.add(resume)
        db.session.commit()
    except:
        db.session.rollback()

    return text

def makeABTest(user_id):
    test_name = fake.text(100)
    hypothesis = fake.text(100)

    test = models.ABTests()
    test.test_name = test_name
    test.hypothesis = hypothesis
    test.user_id = user_id

    try:
        db.session.add(test)
        db.session.commit()
    except:
        db.session.rollback()

    return test.id

def makeRecipes(test_id, resume):
    for x in range(1, 3):
        test_recipe = 'Control' if x == 1 else 'Recipe B'
        recipes = models.Recipes()
        recipe.test_id = test_id
        recipes.recipe = test_recipe

        recipe_b = fake.text(300) + '\n' + fake.text(300) + '\n' + fake.text(300)
        version = resume if test_recipe == 'Control' else recipe_b
        recipes.version = version

        try:
            db.session.add(recipes)
            db.session.commit()
        except:
            db.session.rollback()

def makeJobPosting(poster_id):
    job = models.Jobs()
    job.title = fake.text(50)
    job.description = fake.text(500)
    job.skills = fake.text(50)
    job.url = fake.url()
    job.poster_id = poster_id

    try:
        db.session.add(job)
        db.session.commit()
    except:
        db.session.rollback()