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
str_mos_key=''
dict_launches=dict()
#Request handlers - currently not using templating yet
class MainPage(webapp2.RequestHandler):

    def get(self):
            #self.response.write('<title>A GAE Experiment</title>')
            #self.response.write('Select from the following modes of sale for analysis<br>')
            global str_session_url
            global dict_mos_links
            dict_mos_links,str_session_url=mos.get_dict_mos_links()
            template_values = {
                'dict_mos_links': dict_mos_links,
            }
        
            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))

#prototype landing page after selecting mode of sale (MOS): BTO or SBF
class MOSPage(webapp2.RequestHandler):

    def get(self):
            #here we generate the dictionary again. TO DO: make this dictionary global, possible?
            #dict_mos_links=mos.get_dict_mos_links()

            #logging.info(str_mos_key)
            #self.response.write('You have selected '+str_mos_key+'<br>')
            #self.response.write('The link is'+ self.request.get('MOS_link'))
            global str_session_url
            global dict_mos_links
            global str_mos_key
            global dict_launches
            str_mos_key = self.request.get('MOS_Sel')
            #logging.info(dict_mos_links[str_mos_key])
            dict_launches = mos.gen_dict_roomtype(dict_mos_links[str_mos_key],str_session_url)
            sorted_launchdates = dict_launches.keys()
            sorted_launchdates.sort()
            sorted_launchdates = list(reversed(sorted_launchdates))
            dict_friendly_estate = dict()
            
            #generate a dictionary of friendly names for class name estate_id
            for launchdate in sorted_launchdates:
                dict_friendly_estate[launchdate]=dict()
                for estate in dict_launches[launchdate]:
                    dict_friendly_estate[launchdate][estate] = re.sub('[^a-zA-Z0-0]+','_',estate)


            template_values = {
                'str_mos_key':str_mos_key,
                'sorted_launchdates':sorted_launchdates,
                'dict_launches':dict_launches,
                'dict_friendly_estate':dict_friendly_estate,
            }
        
            template = JINJA_ENVIRONMENT.get_template('MOS.html')
            self.response.write(template.render(template_values))

#prototype landing page after selecting the estate and project
class RoomTypePage(webapp2.RequestHandler):

    def get(self):
            global list_dict_post_data
            global reference_cookie
            global reference_url
            global str_mos_key
            global dict_launches
            
            if str_mos_key == 'Build-To-Order':
                roomtype_link = dict_launches[self.request.get('launchdate')][self.request.get('estate')][self.request.get('project')][self.request.get('roomtype')]
            else:
                roomtype_link = dict_launches[self.request.get('launchdate')][self.request.get('estate')][self.request.get('project')]
            
            reference_url,list_dict_post_data,reference_cookie = mos.gen_list_dict_blocks(roomtype_link)

            template_values = {
                'list_dict_post_data':list_dict_post_data,
            }
        
            template = JINJA_ENVIRONMENT.get_template('roomtype.html')
            self.response.write(template.render(template_values))

#prototype landing page for report generation
class ReportPage(webapp2.RequestHandler):

    def get(self):
            # self.response.write('Hello, Report Page!<br>')
            user_index = int(self.request.get('list_idx'))
            global list_dict_post_data
            global reference_cookie
            global reference_url
            #self.response.write(reference_cookie)
            
            list_unit_values,sold_cnt,total_cnt,ethnic_quota = mos.list_analyse_block(reference_url,reference_cookie,list_dict_post_data,user_index)

            # for block_value in list_block_values:
                # self.response.write(cgi.escape(str(block_value))+'<br>')
            # self.response.write('Units Sold: '+str(sold_cnt)+ ' Total Units '+str(total_cnt))
            template_values = {
                'title': 'Report',
                'list_unit_data': list_unit_values,
                'units_sold': sold_cnt,
                'units_total':total_cnt,
                'list_dict_post_data':list_dict_post_data,
                'ethnic_quota':ethnic_quota.replace("&nbsp;", " "),
                'user_index':user_index,
                
            }
        
            template = JINJA_ENVIRONMENT.get_template('report.html')
            self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([('/', MainPage),('/MOS', MOSPage),('/roomtypepage', RoomTypePage),('/report', ReportPage),],debug=True)

#TODO:
    #1) try not to send entire link in MOSPage - done
#2) inlcude map
#3) Add year based on server date?
    #4) Responsive design - done
    #5) Use templating for mainpage, MOS page and roomtype page - done
#6) Add help '?' popover
#7) Expand block with result without leaving page (i.e., somehow fetch url without leaving page)
