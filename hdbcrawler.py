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

import jinja2
import os


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

#set this to debug, turn off in production (preprocessor?)
#pdb.set_trace()
str_session_url =''
dict_mos_links=dict()
list_dict_post_data=dict()
reference_cookie=''
reference_url=''
#Request handlers - currently not using templating yet
class MainPage(webapp2.RequestHandler):

    def get(self):
			#self.response.write('<title>A GAE Experiment</title>')
			#self.response.write('Select from the following modes of sale for analysis<br>')
			global str_session_url
			global dict_mos_links
			dict_mos_links,str_session_url=mos.get_dict_mos_links()

			template_values = {
				'dict_mos_links': dict_mos_links ,
			}
		
			template = JINJA_ENVIRONMENT.get_template('index.html')
			self.response.write(template.render(template_values))

#prototype landing page after selecting mode of sale (MOS): BTO or SBF
class MOSPage(webapp2.RequestHandler):

    def get(self):
			#here we generate the dictionary again. TO DO: make this dictionary global, possible?
			#dict_mos_links=mos.get_dict_mos_links()
			str_mos_key = self.request.get('MOS_Sel')
			#logging.info(str_mos_key)
			self.response.write('You have selected '+str_mos_key+'<br>')
			#self.response.write('The link is'+ self.request.get('MOS_link'))
			global str_session_url
			global dict_mos_links
			#logging.info(dict_mos_links[str_mos_key])
			dict_launches = mos.gen_dict_roomtype(dict_mos_links[str_mos_key],str_session_url)
			sorted_launchdates = dict_launches.keys()
			sorted_launchdates.sort()
			sorted_launchdates = list(reversed(sorted_launchdates))
			if dict_launches:
				for launchdates in sorted_launchdates:
					self.response.write('<h2>'+launchdates+'</h2>')
					for estates in dict_launches[launchdates]:
						self.response.write('<h3>'+estates+'</h3>')
						for project in dict_launches[launchdates][estates]:
							if str_mos_key == 'Build-To-Order':
								self.response.write(project+'| ')
								for roomtype in dict_launches[launchdates][estates][project]:
									self.response.write('<a href="/roomtypepage?roomtype_link='+dict_launches[launchdates][estates][project][roomtype].replace("&","%26")+'">'+roomtype+'</a> | ')
								self.response.write('<br>')
							else:
								#this is for the Sale of balance case, where there are actually no "project" names,
								#hence [project] key actually refers to the [roomtype]
								self.response.write('<a href="/roomtypepage?roomtype_link='+dict_launches[launchdates][estates][project].replace("&","%26")+'">'+project+'</a> | ')
					self.response.write('<br><br>')
			self.response.write('<br><footer>Created by Timothy Teh | Engineer | Inventor | Experimentalist | &#169; 2014 All Rights Reserved. </footer>')
#prototype landing page after selecting the estate and project
class RoomTypePage(webapp2.RequestHandler):

    def get(self):
			#self.response.headers['Content-Type'] = 'text/plain'
			#self.response.write('Hello, RoomType Page!<br>')
			
			#prototype
			# str_roomtype_url = self.request.get('roomtype_link')
			# self.response.write(str_roomtype_url+'<br>')
			# obj_flattype = re.search('&ft=(.*)&',str_roomtype_url)
			# self.response.write('ft is '+obj_flattype.groups()[0]+'<br>')
			# self.response.write('twn is '+ re.search('twn=(.*)',str_roomtype_url).groups()[0]+'<br>')
			#end of prototype

			global list_dict_post_data
			global reference_cookie
			global reference_url
			reference_url,list_dict_post_data,reference_cookie = mos.gen_list_dict_blocks(self.request.get('roomtype_link'))
			self.response.write('Click on the blocks to analyse<br>')
			for idx,dict_post_data in enumerate(list_dict_post_data):
				self.response.write('<a href="/report?list_idx='+str(idx)+'">'+dict_post_data['Block']+'</a><br>')
			self.response.write('<br><footer>Created by Timothy Teh | Engineer | Inventor | Experimentalist | &#169; 2014 All Rights Reserved. </footer>')

#prototype landing page for report generation
class ReportPage(webapp2.RequestHandler):

    def get(self):
			# self.response.write('Hello, Report Page!<br>')
			user_index = int(self.request.get('list_idx'))
			global reference_cookie
			global reference_url
			#self.response.write(reference_cookie)
			
			list_unit_values,sold_cnt,total_cnt,ethnic_quota = mos.list_analyse_block(reference_url,reference_cookie,list_dict_post_data,user_index)
			self.response.write('Block '+list_dict_post_data[user_index]['Block']+', '+list_dict_post_data[user_index]['Flat']+', '+list_dict_post_data[user_index]['Town']+'<br>')
			self.response.write('Ethnic Quota: '+ethnic_quota)
			# for block_value in list_block_values:
				# self.response.write(cgi.escape(str(block_value))+'<br>')
			# self.response.write('Units Sold: '+str(sold_cnt)+ ' Total Units '+str(total_cnt))
			template_values = {
				'title': 'Report',
				'list_unit_data': list_unit_values,
				'units_sold': sold_cnt,
				'units_total':total_cnt,
			}
		
			template = JINJA_ENVIRONMENT.get_template('report.html')
			self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([('/', MainPage),('/MOS', MOSPage),('/roomtypepage', RoomTypePage),('/report', ReportPage),],debug=True)

#TODO:
#1) try not to send entire link in MOSPage
#2) inlcude map
#3) Add year based on server date?
#4) Responsive design
#5) Use templating for mainpage, MOS page and roomtype page