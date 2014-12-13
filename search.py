from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import *
from whoosh.qparser import MultifieldParser
import os
from app import db
import models

candidates = Schema(user_id=ID(stored=True), tagline=TEXT(stored=True), summary=TEXT(stored=True), experience=TEXT(stored=True))
jobs = Schema(job_id=ID(stored=True), title=TEXT(stored=True), skills=TEXT(stored=True), description=TEXT(stored=True))

if not os.path.exists('jobs_index'):
    os.makedirs('jobs_index')

if not os.path.exists('candidates_index'):
    os.makedirs('candidates_index')

try:
    jobs_ix = open_dir('jobs_index')
except:
    print "re-creating jobs index"
    jobs_ix = create_in('jobs_index', jobs)

try:
    candidate_ix = open_dir('candidates_index')
except:
    print "re-creating candidate index"
    candidate_ix = create_in('candidates_index', candidates)

def reIndexJobs():
    try:
        jobs_ix = create_in('jobs_index', jobs)
        jobs_data = db.session.query(models.Jobs).all()
        writer = jobs_ix.writer()
        for job in jobs_data:
            writer.add_document(job_id=unicode(str(job.id)), title=job.title, skills=job.skills, description=job.description)

        writer.commit()
        return True
    except:
        return False

def addJob(job_id):
    writer = jobs_ix.writer()
    job = db.session.query(models.Jobs).filter_by(id=job_id).first()
    try:
        writer.add_document(job_id=unicode(str(job.id)), title=job.title, skills=job.skills, description=job.description)
        writer.commit()
        return True
    except Exception as e:
        print "Error adding job: ", e
        return False

def reIndexCandidates():
    try:
        candidates_ix = create_in('candidates_index', candidates)
        candidate_data = db.session.query(models.User, models.Resume).join(models.Resume).all()
        writer = candidates_ix.writer()

        #data is in tuples
        for candidate in candidate_data:
            writer.add_document(user_id=unicode(str(candidate[0].id), "utf-8"), tagline=candidate[0].tagline, summary=candidate[0].summary, experience=candidate[1].resume)
        writer.commit()
        return True
    except Exception as err_msg:
        print "Error reindexing: %s" % err_msg
        return False

def addCandidate(user_id):
    writer = candidate_ix.writer()
    candidate = db.session.query(models.User, models.Resume).join(models.Resume).filter_by(user_id=user_id).first()
    try:
        writer.add_document(user_id=unicode(str(candidate[0].id), "utf-8"), tagline=candidate[0].tagline, summary=candidate[0].summary, experience=candidate[1].resume)
        writer.commit()
        return True
    except Exception as e:
        print "Error adding candidate: ", e
        return False

#c_writer = candidate_ix.writer()
#j_writer = jobs_ix.writer()

#c_writer.commit()


#j_writer.commit()
#j_writer.add_document(job_id=u"1", title=u"Sr. Job Maker", skills=u"Money, SQL, jobs, programming", description=u"foo foo in the poo poo")

#
#with s.jobs_ix.searcher() as searcher:
#    query = QueryParser("title", s.jobs_ix.schema).parse("job")
#    results = searcher.search(query)
#    results[0]

def candidateSearch(term):
    searcher = candidate_ix.searcher()
    query = MultifieldParser(["user_id", "tagline", "summary", "resume"], schema=candidate_ix.schema).parse(term)
    results = searcher.search(query)
    return results

def jobSearch(term):
    searcher = jobs_ix.searcher()
    query = MultifieldParser(["job_id", "title", "skills", "description"], schema=jobs_ix.schema).parse(term)
    results = searcher.search(query)
    return results
#with s.jobs_ix.searcher() as searcher:
#    query = QueryParser("job_id", s.jobs_ix.schema).parse("1")
#    results = searcher.search(query)
#    results[0]