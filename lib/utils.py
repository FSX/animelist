#!/usr/bin/python

# =============================================================================
# lib/utils.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import thread
import cPickle

# Cache data with cPickle
def cache_data(path, data):
    with open(path, 'wb') as f:
        cPickle.dump(data, f)

# Get data from cache file with cPickle
def get_cache(path):
    with open(path, 'rb') as f:
        contents = cPickle.load(f)

    return contents

# Decode htmlentities
def htmldecode(string):
    return string.replace('&apos;', '\'')

# Wrapper for thread.start_new_thread()
def sthread(function, args):
    thread.start_new_thread(function, args)
