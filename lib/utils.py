#!/usr/bin/python

# =============================================================================
# lib/utils.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os
import cPickle

import gtk

def cache_data(path, data):
    "Cache data with cPickle."

    with open(path, 'wb') as f:
        cPickle.dump(data, f, cPickle.HIGHEST_PROTOCOL)

def get_cache(path):
    "Get data from cache file with cPickle."

    with open(path, 'rb') as f:
        contents = cPickle.load(f)

    return contents

def htmldecode(string):
    "Decode htmlentities."

    return string.replace('&apos;', '\'')

def get_image(image):
    "Returns a gtk.gdk.Pixbuf."

    if os.access(image, os.F_OK):
        return gtk.gdk.pixbuf_new_from_file(image)
