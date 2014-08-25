import webapp2
from google.appengine.ext.webapp import template
import urllib2
import urllib
import re
#for debug
#import pdb
import sys
import mos
import logging
import cgi
#set this to debug, turn off in production (preprocessor?)
#pdb.set_trace()
str_session_url =''
dict_mos_links=dict()
#Request handlers - currently not using templating yet
class MainPage(webapp2.RequestHandler):

    def get(self):
			self.response.write('Select from the following modes of sale for crawling<br>')
			global str_session_url
			global dict_mos_links
			dict_mos_links,str_session_url=mos.get_dict_mos_links()
			for mos_name in dict_mos_links:
				self.response.write('<a href="/MOS?MOS_Sel='+mos_name+'">'+mos_name+'</a><br>')
				#self.response.write('<a href="'+dict_mos_links[mos_name]+'">'+mos_name+'</a><br>')
			#self.response.headers['Content-Type'] = 'text/plain'
			#self.response.out.write(template.render('index.html',{}))
			self.response.write('<footer>Created by Timothy Teh 2014 All Rights Reserved &#169;</footer>')

#prototype landing page after selecting mode of sale (MOS): BTO or SBF
class MOSPage(webapp2.RequestHandler):

    def get(self):
			#here we generate the dictionary again. TO DO: make this dictionary global, possible?
			#dict_mos_links=mos.get_dict_mos_links()
			str_mos_key = self.request.get('MOS_Sel')
			logging.info(str_mos_key)
			self.response.write('Hello, MOS Page!<br>You have selected '+str_mos_key+'<br>')
			#self.response.write('The link is'+ self.request.get('MOS_link'))
			global str_session_url
			global dict_mos_links
			logging.info(dict_mos_links[str_mos_key])
			dict_launches = mos.gen_dict_roomtype(dict_mos_links[str_mos_key],str_session_url)
			if dict_launches:
				for launchdates in dict_launches:
					self.response.write('<h2>'+launchdates+'</h2>')
					for estates in dict_launches[launchdates]:
						self.response.write('<h3>'+estates+'</h3>')
						for project in dict_launches[launchdates][estates]:
							if str_mos_key == 'Build-To-Order':
								self.response.write(project+'<br>')
								for roomtype in dict_launches[launchdates][estates][project]:
									self.response.write('<a href="/roomtypepage?roomtype_link='+dict_launches[launchdates][estates][project][roomtype].replace("&","%26")+'">'+roomtype+'</a><br>')
							else:
								#this is for the Sale of balance case, where there are actually no "project" names,
								#hence [project] key actually refers to the [roomtype]
								self.response.write('<a href="/roomtypepage?roomtype_link='+dict_launches[launchdates][estates][project].replace("&","%26")+'">'+project+'</a><br>')
			self.response.write('<footer>Created by Timothy Teh 2014 All Rights Reserved &#169;</footer>')
#prototype landing page after selecting the estate and project
class RoomTypePage(webapp2.RequestHandler):

    def get(self):
			#self.response.headers['Content-Type'] = 'text/plain'
			self.response.write('Hello, RoomType Page!<br>')
			
			#prototype
			str_roomtype_url = self.request.get('roomtype_link')
			self.response.write(str_roomtype_url+'<br>')
			obj_flattype = re.search('&ft=(.*)&',str_roomtype_url)
			self.response.write('ft is '+obj_flattype.groups()[0]+'<br>')
			self.response.write('twn is '+ re.search('twn=(.*)',str_roomtype_url).groups()[0]+'<br>')
			#end of prototype
			self.response.write('<a href="'+mos.gen_dict_blocks(self.request.get('roomtype_link'))+'">'+obj_flattype.groups()[0]+'</a><br>')
			self.response.write(cgi.escape(mos.gen_dict_blocks(self.request.get('roomtype_link'))))
			self.response.write('<footer>Created by Timothy Teh 2014 All Rights Reserved &#169;</footer>')

#prototype landing page for report generation
class ReportPage(webapp2.RequestHandler):

    def get(self):
			self.response.write('Hello, Report Page!')

app = webapp2.WSGIApplication([('/', MainPage),('/MOS', MOSPage),('/roomtypepage', RoomTypePage),('/report', ReportPage),],debug=True)
