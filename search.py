from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import *
from whoosh.qparser import MultifieldParser
import os
from app import db
import models

candidates = Schema(user_id=ID(stored=True), tagline=TEXT(stored=True), summary=TEXT(stored=True), experience=TEXT(stored=True), skills=TEXT(stored=True))
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

#need to write refresh def for index
def reIndexCandidates():
    candidates_ix = create_in('candidates_index', candidates)
    candidate_data = db.session.query(models.User, models.Resume).join(models.Resume).all()
    writer = candidates_ix.writer()

    #data is in tuples
    for candidate in candidate_data:
        writer.add_document(user_id=unicode(str(candidate[0].id), "utf-8"), tagline=candidate[0].tagline, summary=candidate[0].summary, experience=candidate[1].experience, skills=candidate[1].skills)
    writer.commit()
    return True

def addCandidate(user_id):
    writer = candidate_ix.writer()
    candidate = db.session.query(models.User, models.Resume).join(models.Resume).filter_by(user_id=user_id).first()
    try:
        writer.add_document(user_id=unicode(str(candidate[0].id), "utf-8"), tagline=candidate[0].tagline, summary=candidate[0].summary, experience=candidate[1].experience, skills=candidate[1].skills)
        writer.commit()
        return True
    except:
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

#Schema(user_id=ID(stored=True), tagline=TEXT(stored=True), summary=TEXT(stored=True), experience=TEXT(stored=True), skills=TEXT(stored=True))
def candidateSearch(term):
    searcher = candidate_ix.searcher()
    query = MultifieldParser(["user_id", "tagline", "summary", "experience", "skills"], schema=candidate_ix.schema).parse(term)
    results = searcher.search(query)
    return results
#with s.jobs_ix.searcher() as searcher:
#    query = QueryParser("job_id", s.jobs_ix.schema).parse("1")
#    results = searcher.search(query)
#    results[0]