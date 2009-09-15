#!/usr/bin/python

# =============================================================================
# lib/request.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import urllib
import httplib
import base64

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
