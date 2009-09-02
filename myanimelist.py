#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================================================================
# myanimelist.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os
import sys
import urllib
import httplib
import base64
import xml.etree.cElementTree as et
import htmlentitydefs
import re

from modules import utils

class Mal():
    def __init__(self, al):
        self.al = al

    #
    #  Fetch/Download aime list from MAL
    #
    def fetch_list(self):

        try:
            response = self._request('/malappinfo.php?u=' + urllib.quote(self.al.config.settings['username']) + '&status=all&type=anime')
        except (HttpRequestError, HttpStatusError):
            return False

        return response

    #
    #  Parse the xml data that contains the anime list from MAL
    #
    def parse_list(self, xml_data):

        parsed_list = {}
        tree = et.fromstring(xml_data)
        branches = tree.getchildren()

        for branch in branches:
            if branch.tag == 'anime':

                leaves = branch.getchildren()
                parsed_list[int(leaves[0].text)] = [
                    leaves[0].text,                    # 0 = Anime ID
                    utils.htmldecode(leaves[1].text),  # 1 = Title
                    leaves[3].text,                    # 2 = Type
                    leaves[13].text,                   # 3 = Score
                    leaves[14].text,                   # 4 = Status

                    leaves[10].text,                   # 5 = Watched episodes
                    leaves[4].text                     # 6 = Episodes
                    ]

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

        try:
            response = self._request('api/anime/search.xml?q=' + urllib.quote(search_query), authenticate=True)
        except (HttpRequestError, HttpStatusError):
            return False

        # Convert entities to prevent cElementTree from spitting out erros
        response = unquotehtml(response)

        #try:
        tree = et.fromstring(response)
        #except SyntaxError:
        #    print response
        #    return False

        parsed_list = {}
        branches = tree.getchildren()

        for branch in branches:
            leaves = branch.getchildren()
            parsed_list[int(leaves[0].text)] = [
                leaves[0].text,                    # 0 = Anime ID
                utils.htmldecode(leaves[1].text),  # 1 = Title
                leaves[6].text,                    # 2 = Type
                leaves[4].text,                    # 3 = Episodes
                leaves[5].text                     # 4 = Score

                #leaves[14].text,                   # 4 = Status
                #leaves[10].text,                   # 5 = Watched episodes
                #leaves[4].text                     # 6 = Episodes
                ]

        return parsed_list

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

        try:
            request = connection.request(method.upper(), '/' + path, params, headers)

            response = connection.getresponse()

            if response.status != httplib.OK:
                connection.close()
                raise HttpStatusError()

            response_read = response.read()
            connection.close()

            return response_read
        except:
            raise HttpRequestError()

#
#  Convert a HTML entity into normal string (ISO-8859-1
#  http://groups.google.com/group/comp.lang.python/browse_thread/thread/7f96723282376f8c/
#
def convertentity(m):

    if m.group(1) == '#':
        try:
            return chr(int(m.group(2)))
        except ValueError:
            return '&#%s;' % m.group(2)
    try:
        return htmlentitydefs.entitydefs[m.group(2)]
    except KeyError:
        return '&%s;' % m.group(2)

#
#  Convert a HTML quoted string into normal string (ISO-8859-1).
#  Works with &#XX; and with &nbsp; &gt; etc.
#  http://groups.google.com/group/comp.lang.python/browse_thread/thread/7f96723282376f8c/
#
def unquotehtml(s):
    return re.sub(r'&(#?)(.+?);', convertentity, s)

#
#  Exceptions
#
class HttpRequestError(Exception):
    pass

class HttpStatusError(Exception):
    pass
