import urllib2
import urllib
import re
import logging
import cgi
import HTMLParser


#comment out for production
from google.appengine.api import urlfetch
urlfetch.set_default_fetch_deadline(60)
#end

#import pdb
#pdb.set_trace()
def get_dict_mos_links():

    # headers = {'User-agent' :'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}
    # url = "http://www.hdb.gov.sg/fi10/fi10321p.nsf/w/BuyingNewFlatShortlistedApplicants?OpenDocument"
    # req = urllib2.Request(url,None,headers)
    # response = urllib2.urlopen(req)
    # the_page = response.read()
    # #print the_page

    # #get the line containing links
    # for line in the_page.splitlines():
        # if "Mode of Sale" in line:
            # linkstr = line
    # #The following code gets the str_session_url, which is the first URL from which the JSESSIONIDv7 cookie is initialized
    # #<iframe name="FRAME1" height="2200" width="100%" frameborder=0 scrolling=auto src="http://services2.hdb.gov.sg/webapp/BP13INTV/BP13SFlatAvailability?sel=BTO"></iframe>
    # str_session_url = re.search('<iframe name.*src="(.*)"></iframe>',the_page).groups()[0]

    # #print linkstr
    # mlist = re.finditer('javascript:loadURL\(\'(.*?)\'\)">(.*?)</a>', linkstr)
    # #generate a dictionary of links of mode of sales
    dict_mos_links = dict()
    # for m in mlist:
        # dict_mos_links[m.groups()[1]] = m.groups()[0]
    dict_mos_links['Build-To-Order'] = "http://services2.hdb.gov.sg/webapp/BP13AWFlatAvail/BP13SEstateSummary?sel=BTO"
    dict_mos_links['Sale of Balance Flats'] = "http://services2.hdb.gov.sg/webapp/BP13AWFlatAvail/BP13SEstateSummary?sel=SBF"
    str_session_url = "http://services2.hdb.gov.sg/webapp/BP13AWFlatAvail/BP13SEstateSummary?sel=BTO"
    return dict_mos_links,str_session_url

def gen_dict_roomtype(user_select_url,session_url):
    h = HTMLParser.HTMLParser()
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
        
    #logging.info(server_url)
    server_url = 'http://services2.hdb.gov.sg'
    #split the content by launchdates
    list_launches = contents.split('<h4>')
    
    #remove first item - no use
    list_launches.pop(0)
    #generate an empty dictionary launches
    dict_launches = dict()
    
    #There are 2 different algorithms for sale of balance and build to order. Currently I can't think of
    #a more general algo, so this is the best option for now
    for launch in list_launches:
        #generate keys for dict_launches
        resobj_launchdate = re.search('(.*?)</h4>',launch)
        try:
            
            dictkey_launchdate = resobj_launchdate.groups()[0]
            #initialize dict_launches
            dict_launches[dictkey_launchdate] = dict()
        except:
            #print 'launchdate not found'
            return None

        #split launchdate by estates
        list_estates = launch.split('<h5>')
        list_estates.pop(0)

        for estate in list_estates:
            #generate key for dict_launches:estate
            obj_estate_names = re.search('(.*?)</h5>',estate)
            dictkey_estate = obj_estate_names.groups()[0]

            #initialize dict_launches:estate
            dict_launches[dictkey_launchdate][dictkey_estate] = dict()
            
            list_project_names = re.findall('<td colspan="6"><b>(.*?)</b></td>', estate)
            
            #for BTO
            if list_project_names:
                #split estate by projects - find the project for each estate
                list_projects = estate.split('<td colspan="6">')
                list_projects.pop(0)
                for project in list_projects:
                    #generate key for dict_launches:estate:project
                    obj_project_names = re.search('<b>(.*?)</b>',project)
                    dictkey_project = h.unescape(obj_project_names.groups()[0])
                    #print dictkey_project
                    
                    #initialize dict_launches:estate:project
                    dict_launches[dictkey_launchdate][dictkey_estate][dictkey_project] = dict()
                    #generate the key and value for dict_launches:estate:project:roomtype
                    mlist = re.finditer('openmypage\((.*?)\)\'>?(.*?)</a></td>',project)
                    
                    #generate the dictionary dict_launches:estate:project:roomtype
                    for m in mlist:
                        dictval_roomtype = str(h.unescape(m.groups()[0].split(',')[0].strip('"'))) 
                        dictkey_roomtype = m.groups()[1]
                        dict_launches[dictkey_launchdate][dictkey_estate][dictkey_project][dictkey_roomtype]=server_url+dictval_roomtype
                    #logging.info(dict_launches[dictkey_launchdate][dictkey_estate][dictkey_project][dictkey_roomtype])
                    #print dict_launches[dictkey_launchdate][dictkey_estate][dictkey_project][dictkey_roomtype]
            else:
                mlist = re.finditer('openmypage\((.*?)\)\'>?(.*?)</a></td>',estate)
                #generate the dictionary dict_launches:estate:roomtype
                for m in mlist:
                    #logging.info(m.groups()[0])
                    dictval_roomtype = str(h.unescape(m.groups()[0]))
                    dictval_roomtype = dictval_roomtype.split(',')[0].strip('"')
                    #logging.info(dictval_roomtype)
                    dictkey_roomtype = m.groups()[1]
                    #logging.info(dictkey_roomtype)
                    dict_launches[dictkey_launchdate][dictkey_estate][dictkey_roomtype]=server_url+dictval_roomtype

    return dict_launches

def gen_list_dict_blocks(str_roomtype_url):
    headers = {'User-agent' :'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}
    server_url = re.search('(.*)/.*?\?',str_roomtype_url).groups()[0]
    req = urllib2.Request(str_roomtype_url.replace(' ','%20'),None,headers)
    #logging.info(str_roomtype_url)
    response = urllib2.urlopen(req)
    str_cookies = response.info().getheader('Set-Cookie')
    session_cookie= re.search('(JSESSIONIDv7=.*?;)',str_cookies).groups()[0]
    contents = response.read()

    #get the ajax query
    ajax_url = re.search('ajax\({.*url.*?"(.*?)",.*}', contents, re.DOTALL).groups()[0]
    
    server_ajax_url = server_url + '/' + ajax_url
    
    req = urllib2.Request(server_ajax_url, None, headers)
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

    return (server_ajax_url).split('?')[0],list_dict_post_data,session_cookie

def list_analyse_block(reference_url,reference_cookie,dict_post_data):
    headers = {'User-agent' :'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}
    post_data = urllib.urlencode(dict_post_data)

    req = urllib2.Request(reference_url, post_data, headers)
    req.add_header('Cookie',reference_cookie)
    response = urllib2.urlopen(req)
    contents = response.read()
    #logging.info(contents)
    
    ajax_url = re.search('ajax\({.*url.*?"(.*?)",.*}', contents, re.DOTALL).groups()[0]
    
    result_url = reference_url.rsplit('/',1)[0]
    
    result_ajax_url = result_url + '/' + ajax_url
    
    req = urllib2.Request(result_ajax_url, None, headers)
    #req.add_header('Referer', 'http://services2.hdb.gov.sg/webapp/BP13AWFlatAvail/BP13EBSBULIST4')
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