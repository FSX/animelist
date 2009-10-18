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

try:
    import json
except ImportError:
    import simplejson as json

import utils

class MAL():

    def __init__(self, config):

        self.username, self.password, self.host, self.user_agent = config
        self.request = Request(config)

        self.anime = None
        self.manga = None

    def init_anime(self):
        self.anime = Anime(self.username, self.request)

    def init_manga(self):
        pass

    def verify_user(self):

        try:
            self.request.execute(path='account/verify_credentials', authenticate=True)
        except (HttpRequestError, HttpStatusError):
            return False

        return True

class Anime():

    def __init__(self, username, request):

        self.username = username
        self.request = request

    def list(self):
        "Fetch/Download anime list from MAL."

        try:
            response = self.request.execute(path='animelist/%s' % urllib.quote(self.username), authenticate=True)
        except (HttpRequestError, HttpStatusError):
            return False

        # All the data goes into a new dict
        response_data = json.loads(response)['anime']
        data = {}

        for e in response_data:
                data[int(e['id'])] = {
                    'id':               int(e['id']),
                    'title':            utils.htmldecode(e['title']),
                    'type':             e['type'],             # TV, Movie, OVA, ONA, Special, Music
                    'episodes':         int(e['episodes']),
                    'status':           e['status'],           # finished airing, currently airing, not yet aired
                    'watched_status':   e['watched_status'],   # watching, completed, on-hold, dropped, plan to watch
                    'watched_episodes': int(e['watched_episodes']),
                    'score':            int(e['score']),
                    'image':            e['image_url']
                    }

        response_data = None

        return data

    def search(self, query):
        "Fetch/Download anime list from MAL."

        try:
            response = self.request.execute(path='anime/search?q=%s' % urllib.quote(query), authenticate=True)
        except (HttpRequestError, HttpStatusError):
            return False

        # All the data goes into a new dict to keep because the API
        # doesn't provide all the information yet.
        response_data = json.loads(response)
        data = {}

        for e in response_data:
                data[int(e['id'])] = {
                    'id':               int(e['id']),
                    'title':            utils.htmldecode(e['title']),
                    'type':             e['type'],             # TV, Movie, OVA, ONA, Special, Music
                    'episodes':         int(e['episodes']),
                    'status':           e['status'],           # finished airing, currently airing, not yet aired
                    'members_score':    float(e['members_score']),
                    'image':            e['image_url']
                    }

        return data

    def add(self, params):
        "Add anime to list. params = (id, status, episodes, score)."

        try:
            response = self.request.execute(path='animelist/anime', params=params, method='POST', authenticate=True)
        except (HttpRequestError, HttpStatusError):
            return False

        return response

    def update(self, id, params):
        "Update anime in the list. data = {status, episodes, score}."

        try:
            response = self.request.execute(path='animelist/anime/%s' % id, params=params, method='PUT', authenticate=True)
        except (HttpRequestError, HttpStatusError):
            return False

        return response

    def delete(self, id):
        "Remove anime from the list."

        try:
            response = self.request.execute(path='animelist/anime/%s' % id, method='DELETE', authenticate=True)
        except (HttpRequestError, HttpStatusError):
            return False

        # Note: Do 'return response' to return the details of the removed anime.
        # The returned details could be used to make an undo function.
        return True

    def details(self, id):
        "Get information about an anime."

        try:
            response = self.request.execute(path='anime/%s' % id, authenticate=True)
        except (HttpRequestError, HttpStatusError):
            return False

        return json.loads(response)

    def image(self, url):
        "Get the image of the anime."

        return self.request.retrieve(url)

class Request():

    def __init__(self, config):
        self.username, self.password, self.host, self.user_agent = config

    def retrieve(self, url):

        try:
            filename, unused = urllib.urlretrieve(url)
        except urllib.ContentTooShortError:
            return False

        return filename

    def execute(self, path, params=None, method='GET', authenticate=False, ssl=False):

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

# Request Exceptions

class HttpRequestError(Exception):
    pass

class HttpStatusError(Exception):
    pass
