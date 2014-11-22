import urllib as u
import urllib2 as u2
from lxml import etree

publisher_id = 7837020139926262
query = {}
indeed_url = 'http://api.indeed.com/ads/apisearch?'
#startVal = 0

def buildQuery(job, start):
	query['q'] = job
	query['l'] = 'san diego, ca'
	query['v'] = 2
	query['publisher'] = publisher_id
	query['start'] = start
	query['limit'] = 5

	query_string = u.urlencode(query)

	return indeed_url + query_string


def getResponse(query):
	req = u2.Request(query)
	response = u2.urlopen(req)
	data = response.read()
	return data


def parseXML(data):
	root = etree.fromstring(data)
	#for element in root.iter():
	#	print "%s - %s" % (element.tag, element.text)
	#use jobkey for community  page
		
	return root

#data.xpath('/response/totalresults')  #list type
#titles = data.xpath('/response/results/result/jobtitle')
def getTree(job, start):
	q = buildQuery(job, start)
	resp = getResponse(q)
	data = parseXML(resp)
	return data


#--------------------------------------------------------------------
#
#				Parsing functions to use on the site.
#
#--------------------------------------------------------------------
def getTotalResults(data):
	total = data.xpath('/response/totalresults')
	num = total[0].text
	return num


#Easier to return all results
def getResults(data):
	results = data.xpath('/response/results/result')
	return results