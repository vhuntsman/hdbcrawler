import webapp2
from google.appengine.ext.webapp import template
import urllib2
import urllib



class MainPage(webapp2.RequestHandler):

    def get(self):
        
			url = "http://www.hdb.gov.sg/fi10/fi10321p.nsf/w/BuyingNewFlatShortlistedApplicants?OpenDocument"

			req = urllib2.Request(url)
			response = urllib2.urlopen(req)
			the_page = response.read()
			self.response.headers['Content-Type'] = 'text/plain'
			self.response.write(the_page)
			#self.response.out.write(template.render('index.html',{}))

class SubPage(webapp2.RequestHandler):

    def get(self):
			self.response.write('Hello, world!')

app = webapp2.WSGIApplication([('/', MainPage),('/next', SubPage),],debug=True)

#app = webapp2.WSGIApplication([('/', MainPage),],debug=True)