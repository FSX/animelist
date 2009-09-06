#!/usr/bin/python

# =============================================================================
# lib/myanimelist.py
# This module is made for the Unofficial MAL API: http://mal-api.com/
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os
import sys
import urllib
import httplib
import base64
import json

import utils

class Anime():

    def __init__(self, config):

        self.username, self.password, self.host, self.user_agent = config
        self.request = Request(config)

    #
    #  Fetch/Download anime list from MAL
    #
    def list(self):

        try:
            response = self.request.do(path='animelist/%s' % urllib.quote(self.username), authenticate=True)
        except (HttpRequestError, HttpStatusError):
            return False

        # All the data goes into a new dict to keep because the API
        # doesn't provide all the information yet.
        response_data = json.loads(response)['anime']
        data = {}

        for e in response_data:
                data[int(e['id'])] = {
                    'id':               e['id'],
                    'title':            utils.htmldecode(e['title']),
                    'type':             e['type'],             # TV, Movie, OVA, ONA, Special, Music
                    'episodes':         e['episodes'],
                    'status':           e['status'],           # finished airing, currently airing, not yet aired
                    'watched_status':   e['watched_status'],   # watching, completed, on-hold, dropped, plan to watch
                    'watched_episodes': e['watched_episodes'],
                    'score':            e['score']
                    }

        response_data = None

        return data


    #
    #  Add anime to list. data = (status, episodes, score)
    #
    def add(self, id, data):
        pass

    #
    #  Update anime in the list. data = (status, episodes, score)
    #
    def update(self, id, data):

        params = {'status': data[0], 'episodes': data[1],'score': data[2]}

        try:
            response = self.request.do(path='animelist/anime/%s' % id, params=params, method='PUT', authenticate=True)
        except (HttpRequestError, HttpStatusError):
            return False

        return response

    #
    #  Remove anime from the list
    #
    def delete(self, id):

        try:
            response = self.request.do(path='animelist/anime/%s' % id, method='DELETE', authenticate=True)
        except (HttpRequestError, HttpStatusError):
            return False

        return response

class Request():

    def __init__(self, config):
        self.username, self.password, self.host, self.user_agent = config

    #
    #  Do a request
    #
    def do(self, path, params=None, method='GET', authenticate=False, ssl=False):

        headers = {'User-Agent': self.user_agent}

        if method == 'POST':
            headers['Content-type'] = 'application/x-www-form-urlencoded'

        if params is not None:
            params = urllib.urlencode(params)

        if authenticate == True:
            encoded = base64.encodestring('%s:%s' % (self.username, self.password))[:-1]
            headers['Authorization'] = 'Basic %s' % encoded

        if ssl == True:
            connection = httplib.HTTPSConnection(self.host)
        else:
            connection = httplib.HTTPConnection(self.host)

        try:
            request = connection.request(method.upper(), '/' + path, params, headers)
            response = connection.getresponse()

            # Raise an exception if the status code is something else then 200
            if response.status != httplib.OK:
                connection.close()
                raise HttpStatusError()

            response_read = response.read()
            connection.close()

            return response_read
        except:
            raise HttpRequestError()

#
#  Exceptions
#
class HttpRequestError(Exception):
    pass

class HttpStatusError(Exception):
    pass
