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
import ast
from datetime import datetime

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

#set this to debug, turn off in production (preprocessor?)
#pdb.set_trace()

#Request handlers - currently not using templating yet
class MainPage(webapp2.RequestHandler):

    def get(self):
            #self.response.write('<title>A GAE Experiment</title>')
            #self.response.write('Select from the following modes of sale for analysis<br>')
            dict_mos_links,str_session_url=mos.get_dict_mos_links()
            template_values = {
                'dict_mos_links': dict_mos_links,
            }
            self.response.set_cookie('ck_session_url', str_session_url)
            self.response.set_cookie('ck_mos_links', str(dict_mos_links))
            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))


#prototype landing page after selecting mode of sale (MOS): BTO or SBF
class MOSPage(webapp2.RequestHandler):

    def get(self):
            #here we generate the dictionary again. TO DO: make this dictionary global, possible?
            #dict_mos_links=mos.get_dict_mos_links()
            str_session_url = self.request.cookies.get("ck_session_url")
            dict_mos_links = ast.literal_eval(self.request.cookies.get("ck_mos_links"))
            #logging.info(str_mos_key)
            #self.response.write('You have selected '+str_mos_key+'<br>')
            #self.response.write('The link is'+ self.request.get('MOS_link'))
            #global dict_launches
            
            str_mos_key = self.request.get('MOS_Sel')
            #set the cookie for next page
            self.response.set_cookie('ck_mos_key', str_mos_key)
            
            #logging.info(dict_mos_links[str_mos_key])
            dict_launches = mos.gen_dict_roomtype(dict_mos_links[str_mos_key],str_session_url)
            #self.response.set_cookie('ck_dict_launches', str(dict_launches))
            
            #build a list of datetime objects from the launch date keys
            list_dt = []
            for launchdate in dict_launches.keys():
                list_dt.append(datetime.strptime(launchdate,'%b %Y'))
            
            #sort the datetime objects
            list_dt.sort()
            #reverse the list
            list_dt = list(reversed(list_dt))
            sorted_launchdates = []
            
            for dt in list_dt:
                sorted_launchdates.append(dt.strftime("%b %Y"))
            
            dict_friendly_estate = dict()
            #generate a dictionary of friendly names for class name estate_id
            for launchdate in sorted_launchdates:
                dict_friendly_estate[launchdate]=dict()
                for estate in dict_launches[launchdate]:
                    dict_friendly_estate[launchdate][estate] = re.sub('[^a-zA-Z0-9]+','_',launchdate)+'_'+re.sub('[^a-zA-Z0-9]+','_',estate)


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
            
    def post(self):
            roomtype_link = self.request.get('pd_roomtype_link')
            #logging.info(roomtype_link)
            reference_url,list_dict_post_data,reference_cookie = mos.gen_list_dict_blocks(roomtype_link)
            
            #Save the data for the next page
            self.response.set_cookie('ck_reference_url', reference_url)
            self.response.set_cookie('ck_reference_cookie', reference_cookie)
            #self.response.set_cookie('ck_post_data', str(list_dict_post_data))
            
            template_values = {
                'list_dict_post_data':list_dict_post_data,
            }
        
            template = JINJA_ENVIRONMENT.get_template('roomtype.html')
            self.response.write(template.render(template_values))

#prototype landing page for report generation
class ReportPage(webapp2.RequestHandler):

    def post(self):
            dict_post_data = ast.literal_eval(self.request.get('pd_dict_post_data'))
            reference_cookie = self.request.cookies.get("ck_reference_cookie")
            reference_url = self.request.cookies.get("ck_reference_url")
            #self.response.write(reference_cookie)
            list_unit_values,sold_cnt,total_cnt,ethnic_quota = mos.list_analyse_block(reference_url,reference_cookie,dict_post_data)

            # for block_value in list_block_values:
                # self.response.write(cgi.escape(str(block_value))+'<br>')
            # self.response.write('Units Sold: '+str(sold_cnt)+ ' Total Units '+str(total_cnt))
            template_values = {
                'title': 'Report',
                'list_unit_data': list_unit_values,
                'units_sold': sold_cnt,
                'units_total':total_cnt,
                'ethnic_quota':ethnic_quota.replace("&nbsp;", " "),
                'dict_post_data':dict_post_data,
            }
        
            template = JINJA_ENVIRONMENT.get_template('report.html')
            self.response.write(template.render(template_values))
    
class Handler404(webapp2.RequestHandler):
    
    def get (self):
        template_values = {
            'custom_404_msg': 'Oops! Sorry, this page is not valid. Try a different URL.',
        }
        template = JINJA_ENVIRONMENT.get_template('404.html')
        self.response.write(template.render(template_values))

#use this handler for maintenance page
class MaintPage(webapp2.RequestHandler):
    
    def get (self):
        template_values = {
        }
        template = JINJA_ENVIRONMENT.get_template('maint.html')
        self.response.write(template.render(template_values))

#Comment the line below and uncomment the line after for maintenance
app = webapp2.WSGIApplication([('/', MainPage),('/MOS', MOSPage),('/roomtypepage', RoomTypePage),('/report', ReportPage),('/.*', Handler404),],debug=True)
#app = webapp2.WSGIApplication([('/.*', MaintPage),],debug=True)
#TODO:
    #1) try not to send entire link in MOSPage - done
#2) inlcude map
#3) Add year based on server date?
    #4) Responsive design - done
    #5) Use templating for mainpage, MOS page and roomtype page - done
#6) Add help '?' popover
#7) Expand block with result without leaving page (i.e., somehow fetch url without leaving page)
#8) The size of cookies has to be managed