#!/usr/bin/python

# =============================================================================
# modules/utils.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import cPickle

#  Cache data with cPickle
def cache_data(path, data):
	#handle = open(path, 'w')
	#cPickle.dump(data, handle)
	#handle.close()

    with open(path, 'w') as f:
        cPickle.dump(data, f)

#  Get data from cache file with cPickle
def get_cache(path):
	#handle = open(path, 'r')
	#cache_contents = cPickle.load(handle)
	#handle.close()

    with open(path, 'r') as f:
        cache_contents = cPickle.load(f)

	return cache_contents

#  Decode htmlentities
def htmldecode(string):
	return string.replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', '\'').replace('&gt;', '>').replace('&lt;', '<')
