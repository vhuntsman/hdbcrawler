import urllib2
import urllib
import re
import logging
import cgi


#comment out for production
#from google.appengine.api import urlfetch
#urlfetch.set_default_fetch_deadline(60)
#end

#import pdb
#pdb.set_trace()
def get_dict_mos_links():

	headers = {'User-agent' :'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}
	url = "http://www.hdb.gov.sg/fi10/fi10321p.nsf/w/BuyingNewFlatShortlistedApplicants?OpenDocument"
	req = urllib2.Request(url,None,headers)
	response = urllib2.urlopen(req)
	the_page = response.read()
	#print the_page

	#get the line containing links
	for line in the_page.splitlines():
		if "Mode of Sale" in line:
			linkstr = line
	#The following code gets the str_session_url, which is the first URL from which the JSESSIONIDv7 cookie is initialized
	#<iframe name="FRAME1" height="2200" width="100%" frameborder=0 scrolling=auto src="http://services2.hdb.gov.sg/webapp/BP13INTV/BP13SFlatAvailability?sel=BTO"></iframe>
	str_session_url = re.search('<iframe name.*src="(.*)"></iframe>',the_page).groups()[0]

	#print linkstr
	mlist = re.finditer('javascript:loadURL\(\'(.*?)\'\)">(.*?)</a>', linkstr)
	#generate a dictionary of links of mode of sales
	dict_mos_links = dict()
	for m in mlist:
		dict_mos_links[m.groups()[1]] = m.groups()[0]
	return dict_mos_links,str_session_url

def gen_dict_roomtype(user_select_url,session_url):
	#opener = urllib2.build_opener()
	#opener.addheaders=[('User-agent', 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36')]
	headers = {'User-agent' :'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}
	
	#generate the session cookie from the session_url
	req = urllib2.Request(session_url,None,headers)
	response = urllib2.urlopen(req)
	str_cookies = response.info().getheader('Set-Cookie')
	session_cookie= re.search('(JSESSIONIDv7=.*?;)',str_cookies).groups()[0]
	
	#request for the user_select_url
	req = urllib2.Request(user_select_url,None,headers)
	req.add_header('Cookie',session_cookie)
	response = urllib2.urlopen(req)
	contents = response.read()
	
	#find the server and links to estate/room
	mlist = re.search('var server=\'(.*?)\';',contents)
	try:
		server_url = mlist.groups()[0]
	except:
		#print 'No Server found'
		return None
	
	#split the content by launchdates
	list_launches = contents.split('svcTableSubHeader')
	
	#remove first item - no use
	list_launches.pop(0)
	#generate an empty dictionary launches
	dict_launches = dict()
	
	#There are 2 different algorithms for sale of balance and build to order. Currently I can't think of
	#a more general algo, so this is the best option for now
	for launch in list_launches:
		#generate keys for dict_launches
		resobj_launchdate = re.search('<td colspan="7" align="left">(.*?)&nbsp;</td>',launch)
		try:
			
			dictkey_launchdate = resobj_launchdate.groups()[0]
			#initialize dict_launches
			dict_launches[dictkey_launchdate] = dict()
		except:
			#print 'launchdate not found'
			return None

		#split launchdate by estates
		list_estates = launch.split('svcTableRowOdd')
		for estate in list_estates:
			#generate key for dict_launches:estate
			obj_estate_names = re.findall('svcTableLabel.*?\>(.*?)&nbsp;',estate)
			if obj_estate_names:
				for estate_name in obj_estate_names:
					#generate keys for dict_launches:estate
					dictkey_estate = estate_name
					#initialize dict_launches:estate
					dict_launches[dictkey_launchdate][dictkey_estate] = dict()
					#split estate by projects - find the project for each estate
					list_projects = estate.split('rowspan')
					list_projects.pop(0)
					for project in list_projects:
						#generate key for dict_launches:estate:project
						obj_project_names = re.search('>(.*?)&nbsp;</td>',project)
						dictkey_project = obj_project_names.groups()[0].strip()
						#print dictkey_project
						
						#initialize dict_launches:estate:project
						dict_launches[dictkey_launchdate][dictkey_estate][dictkey_project] = dict()
						#generate the key and value for dict_launches:estate:project:roomtype
						mlist = re.finditer('openmypagenew2\((.*?)\)\'>?(.*?)</a>&nbsp;</td>',project)
						
						#generate the dictionary dict_launches:estate:project:roomtype
						for m in mlist:
							dictval_roomtype = m.groups()[0].split(',')[0].strip('"')
							dictkey_roomtype = m.groups()[1]
							dict_launches[dictkey_launchdate][dictkey_estate][dictkey_project][dictkey_roomtype]=server_url+dictval_roomtype
							#print dict_launches[dictkey_launchdate][dictkey_estate][dictkey_project][dictkey_roomtype]
			else:
				obj_estate_names = re.findall('rowspan=.*?>(.*?)&nbsp;</td>',estate)
				for estate_name in obj_estate_names:
					#generate keys for dict_launches:estate
					dictkey_estate = estate_name
					#initialize dict_launches:estate
					dict_launches[dictkey_launchdate][dictkey_estate] = dict()
					#split estate by roomtype - find the project for each estate
					list_roomtype = estate.split('rowspan')
					list_roomtype.pop(0)
					for roomtype in list_roomtype:
						#generate the key and value for dict_launches:estate:roomtype
						mlist = re.finditer('openmypagenew2\((.*?)\)\'>?(.*?)</a></td>',roomtype)
						#generate the dictionary dict_launches:estate:roomtype
						for m in mlist:
							dictval_roomtype = m.groups()[0].split(',')[0].strip('"')
							dictkey_roomtype = m.groups()[1]
							dict_launches[dictkey_launchdate][dictkey_estate][dictkey_roomtype]=server_url+dictval_roomtype
							#print dict_launches[dictkey_launchdate][dictkey_estate][dictkey_project][dictkey_roomtype]
	return dict_launches

def gen_list_dict_blocks(str_roomtype_url):
	headers = {'User-agent' :'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}
	req = urllib2.Request(str_roomtype_url,None,headers)
	response = urllib2.urlopen(req)
	contents = response.read()
	#<script language="JavaScript" src="../../14JANBTO_inc_8826/$file/functions.js"></script>
	obj_block_links = re.search('<script language="JavaScript" src="../../(.*functions.js)"></script>',contents)
	#get the flattype from roomtype_url
	flattype = re.search('&ft=(.*)&',str_roomtype_url).groups()[0]
	#get the town from roomtype_url
	town = re.search('twn=(.*)',str_roomtype_url).groups()[0]
	
	#check if the flat type contains '/', e.g., 5-ROOM/3GEN
	if re.search('(/)',flattype):
		str_functions_js = '/'.join(str_roomtype_url.split('/')[:-4])+'/'+obj_block_links.groups()[0]
	else:
		str_functions_js = '/'.join(str_roomtype_url.split('/')[:-3])+'/'+obj_block_links.groups()[0]

	#get the javascript contents
	headers = {'User-agent' :'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}
	req = urllib2.Request(str_functions_js,None,headers)
	response = urllib2.urlopen(req)
	#contents = ''.join(response.read().split())
	contents = response.read()
	
	#find the server url
	server_url = re.search('isgurl.*?=.*?"(.*)";',contents).groups()[0]

	#get the code fragment linking to the blocks
	fragment = re.search('.*\(isgtwn==\''+town+'\'\).*?{(.*?)}',contents,re.DOTALL).groups()[0]
	
	#get the url from the code fragment
	obj_url_link = re.search('\(flattype=="'+flattype+'"\).*?\+.*?\'(.*?)\';',fragment, re.DOTALL)
	if obj_url_link:
		roomtype_url = obj_url_link.groups()[0]
	else:
		#check for SBF style of coding
		#get the url from the code fragment
		obj_url_link = re.search('\(myflattype=="'+flattype+'"\).*?\+.*?\'(.*?)\';',fragment, re.DOTALL)
		if obj_url_link:
			roomtype_url = obj_url_link.groups()[0]
		else:
			obj_url_link = re.search('else.*?\+.*?\'(.*?)\';',fragment, re.DOTALL)
		

	#replace for SBF
	roomtype_url = obj_url_link.groups()[0].replace('\'+myflattype+\'',flattype)
	#replace for BTO
	roomtype_url = roomtype_url.replace('\'+flattype+\'',flattype)

	session_url = server_url+roomtype_url
	#return session_url
	#generate the session cookie from the session_url
	req = urllib2.Request(session_url.replace(' ','%20'),None,headers)
	response = urllib2.urlopen(req)
	str_cookies = response.info().getheader('Set-Cookie')
	session_cookie= re.search('(JSESSIONIDv7=.*?;)',str_cookies).groups()[0]
	session_url_content = response.read()
	
	#generate the url for block request
	#<IFRAME id=search height=340 marginHeight=0 src="/webapp/BP13INTV/BP13EBSBULIST4?Town=Sembawang&Flat_Type=BTO&DesType=A&ethnic=Y&Flat=4-ROOM&ViewOption=A&dteBallot=201403&callPage=&projName=A&BonusFlats=" frameBorder=0 width=420 allowTransparency name=search marginWidth=0></IFRAME>
	str_block_url=re.search('<IFRAME.*src="(.*)".*</IFRAME>',session_url_content,re.DOTALL).groups()[0]
	block_url = str_block_url.replace(' ','%20')
	req = urllib2.Request(server_url+block_url,None,headers)
	req.add_header('Cookie',session_cookie)
	response = urllib2.urlopen(req)
	contents = response.read()

	#return cgi.escape(contents)
	#str_cookies = response.info().getheader('Set-Cookie')
	#session_cookie= re.search('(JSESSIONIDv7=.*?;)',str_cookies).groups()[0]
	blocks = re.finditer('javascript:checkBlk\((.*?)\)',contents,re.DOTALL)
	list_blocks=[]
	for idx,block in enumerate(blocks):
		list_blocks.append(block.groups()[0].split(','))
	#href="javascript:checkBlk('445A','N4','C13')"
	#temp_str = re.search('(href="javascript:checkBlk.*")?',contents,re.DOTALL).groups()[0]
	raw_post_data = re.search('(<input type="hidden" name="Block".*</FORM>)',contents,re.DOTALL).groups()[0]
	#<input type="hidden" name="Block" value="">
	post_data = re.findall('<input type="hidden".*?name="(.*)".*?value="(.*)">',raw_post_data)
	dict_post_data = dict()
	for param in post_data:
		dict_post_data[param[0]]=param[1]
	list_dict_post_data = []
	for idx,block in enumerate(list_blocks):
		list_dict_post_data.append(dict_post_data.copy())
		list_dict_post_data[idx]['Block']=block[0].strip('\'')
		list_dict_post_data[idx]['Neighbourhood']=block[1].strip('\'')
		list_dict_post_data[idx]['Contract']=block[2].strip('\'')

	return (server_url+block_url).split('?')[0],list_dict_post_data,session_cookie

def list_analyse_block(reference_url,reference_cookie,dict_post_data):
	headers = {'User-agent' :'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}
	post_data = urllib.urlencode(dict_post_data)
	post_manual = 'Block=445A&Flat_Type=BTO&Town=Bukit+Batok&Flat=5-ROOM&DesType=A&EthnicA=Y&EthnicM=&EthnicC=&EthnicO=&numSPR=&ViewOption=A&dteBallot=201405&Neighbourhood=N4&Contract=C13&projName=A+++%3BA+++&firstLoadMap=Yes&callPage=esales.hdb.gov.sg&BonusFlats=N'
	req = urllib2.Request(reference_url, post_data, headers)
	req.add_header('Cookie',reference_cookie)
	response = urllib2.urlopen(req)
	contents = response.read()
	#return contents
	CSVlist = []
	SoldUnits = 0
	TotalUnits = 0
	#include the sold units as well
	#logging.info(contents)
	#<td class="textContentNew" colspan="2" nowrap>Malay-10,&nbsp;Chinese-10,&nbsp;Indian/Other Races-4&nbsp;</td>
	str_ethnic_quota = re.search('<td class="textContentNew" colspan="2" nowrap>(Malay.*&nbsp;)</td>',contents,re.DOTALL).groups()[0].strip('&nbsp;')
	#logging.info(str_ethnic_quota)
	for m in re.finditer('.*font class(.*)</div>', contents):
			substring = m.groups()[0]
			CSVSublist = []
			TotalUnits +=1
			#find the unit
			CSVSublist.append(re.match('.*>(.*)</font>.*',substring).groups()[0].strip())
			#find the price and floor area (for a bluetext)
			try:
					CSVSublist.append(re.search('.*nbsp;(.*)</td></tr><tr bgcolor.*',substring).groups()[0])
					try:
						CSVSublist.append(re.search('left;\'>(.*)&nbsp;Sqm</td><',substring).groups()[0])
					except:
						CSVSublist.append(re.search('left;\'>(.*)&nbsp;Sqm(\(3Gen\))</td><',substring).groups()[0]+' '+re.search('left;\'>(.*)&nbsp;Sqm(\(3Gen\))</td><',substring).groups()[1])
			except:
			#append sold and N.A. for a redtext
					SoldUnits +=1
					CSVSublist.append('Sold')
					CSVSublist.append('N.A.')
			CSVlist.append(CSVSublist)
	return CSVlist,SoldUnits,TotalUnits,str_ethnic_quota