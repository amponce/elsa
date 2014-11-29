from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import *
import os

candidates = Schema(user_id=ID(stored=True), tagline=TEXT(stored=True), summary=TEXT(stored=True), experience=TEXT(stored=True), skills=TEXT(stored=True))
jobs = Schema(job_id=ID(stored=True), title=TEXT(stored=True), skills=TEXT(stored=True), description=TEXT(stored=True))

if not os.path.exists('jobs_index'):
    os.makedirs('jobs_index')

if not os.path.exists('candidates_index'):
    os.makedirs('candidates_index')

if not exists_in('jobs_index', 'jobs'):
    jobs_ix = create_in('jobs_index', jobs)
else:
    jobs_ix = open_dir('jobs_index', jobs)

if not exists_in('candidates_index', 'candidates'):
    candidate_ix = create_in('candidates_index', candidates)
else:
    candidate_ix = open_dir('candidates_index', candidates)

c_writer = candidate_ix.writer()
j_writer = jobs_ix.writer()

c_writer.commit()
#j_writer.commit()
#j_writer.add_document(job_id=u"1", title=u"Sr. Job Maker", skills=u"Money, SQL, jobs, programming", description=u"foo foo in the poo poo")

#
#with s.jobs_ix.searcher() as searcher:
#    query = QueryParser("title", s.jobs_ix.schema).parse("job")
#    results = searcher.search(query)
#    results[0]

#with s.jobs_ix.searcher() as searcher:
#    query = QueryParser("job_id", s.jobs_ix.schema).parse("1")
#    results = searcher.search(query)
#    results[0]