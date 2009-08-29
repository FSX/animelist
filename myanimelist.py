#!/usr/bin/python

# =============================================================================
# myanimelist.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os
import sys
import urllib
import urllib2
import httplib
import base64
from xml.dom.minidom import parseString

from modules import utils

class Mal():
    def __init__(self, al):
        self.al = al

        #self.search_anime('bleach')

    #
    #  Fetch/Download aime list from MAL
    #
    def fetch_list(self):

        url = 'http://' + self.al.config.mal['host'] + '/malappinfo.php?u=' + \
            urllib.quote(self.al.config.settings['username']) + \
            '&status=all&type=anime'
        request  = urllib2.Request(url)

        try:                      response = urllib2.urlopen(request)
        except urllib2.HTTPError: return False
        except urllib2.URLError:  return False

        return response.read()

    #
    #  Parse the xml data that contains the anime list from MAL
    #
    def parse_list(self, xml_data):

        parsed_list = {}
        dom         = parseString(xml_data)
        dom_list    = dom.getElementsByTagName('anime')

        # Put data in the list
        for item in dom_list:
            parsed_list[int(item.getElementsByTagName('series_animedb_id')[0].childNodes[0].data)] = [
                item.getElementsByTagName('series_animedb_id')[0].childNodes[0].data,               # 0 = Anime ID
                utils.htmldecode(item.getElementsByTagName('series_title')[0].childNodes[0].data),  # 1 = Title
                item.getElementsByTagName('series_type')[0].childNodes[0].data,                     # 2 = Type
                item.getElementsByTagName('my_score')[0].childNodes[0].data,                        # 3 = Score
                item.getElementsByTagName('my_status')[0].childNodes[0].data,                       # 4 = Status

                item.getElementsByTagName('my_watched_episodes')[0].childNodes[0].data,             # 5 = Watched episodes
                item.getElementsByTagName('series_episodes')[0].childNodes[0].data,                 # 6 = Episodes

                # Extra data
                item.getElementsByTagName('my_id')[0].childNodes[0].data,                           # 7 = My ID
                item.getElementsByTagName('series_image')[0].childNodes[0].data                     # 8 = Image
                ]

        dom.unlink()

        return parsed_list

    #
    #  Download image
    #
    def get_image(self, url):

        filename = os.path.basename(url)

        if not os.path.exists(self.al.HOME + '/' + filename):
            urllib.urlretrieve(url, self.al.HOME + '/' + filename)

        return filename

    #
    #  Add anime to list
    #  data = (episodes, status, score)
    #
    def add_anime(self, id, data):
        pass

    #
    #  Update anime in the list
    #  data = (episodes, status, score)
    #
    def update_anime(self, id, data):

        xml = {'id': int(id), 'data': self._make_xml_values(data)}
        path = 'api/animelist/update/' + str(int(id)) + '.xml'

        return self._request(path, params=xml, method='POST',
            authenticate=True)

    #
    #  Remove anime from the list
    #
    def delete_anime(self, id):
        pass

    #
    #  Search anime
    #
    def search_anime(self, search_query):

        # TODO: Parse xml
        path = 'api/anime/search.xml?q=' + urllib.quote(search_query)
        return self._request(path, authenticate=True)

    #
    #  Make xml values
    #  (episodes, status, score)
    #
    def _make_xml_values(self, data):

        return '''<?xml version="1.0" encoding="UTF-8"?>
<entry>
	<episode>''' + str(int(data[0])) + '''</episode>
	<status>''' + str(int(data[1])) + '''</status>
	<score>''' + str(int(data[2])) + '''</score>
	<downloaded_episodes></downloaded_episodes>
	<storage_type></storage_type>
	<storage_value></storage_value>
	<times_rewatched></times_rewatched>
	<rewatch_value></rewatch_value>
	<date_start></date_start>
	<date_finish></date_finish>
	<priority></priority>
	<enable_discussion></enable_discussion>
	<enable_rewatching></enable_rewatching>
	<comments></comments>
	<fansub_group></fansub_group>
	<tags></tags>
</entry>'''

    #
    #  Make a request
    #
    def _request(self, path, params=None, method='GET', authenticate=False, ssl=False):

        headers = {'User-Agent': self.al.app_name + '/' + self.al.app_version}

        if method == 'POST':
            headers['Content-type'] = 'application/x-www-form-urlencoded'

        if params is not None:
            params = urllib.urlencode(params)

        if authenticate == True:
            encoded = base64.encodestring('%s:%s' % (self.al.config.settings['username'], self.al.config.settings['password']))[:-1]
            headers['Authorization'] = 'Basic %s' % encoded

        if ssl == True: connection = httplib.HTTPSConnection(self.al.config.mal['host'])
        else: connection = httplib.HTTPConnection(self.al.config.mal['host'])

        request = connection.request(method.upper(), '/' + path, params, headers)
        response = connection.getresponse()
        response_read = response.read()

        connection.close()

        return response_read















