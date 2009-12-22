#!/usr/bin/python

# =============================================================================
# config.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os
import base64
import cPickle

import gtk

class Config():

    def __init__(self, al):

        self.al = al
        self.block_access = False
        self.user_verified = True

        # Set default settings
        self.settings = {
            'username': None,
            'password': None,
            'startup_refresh': True,
            'systray': True,
            'window': {
                'x': None,
                'y': None,
                'width': 800,
                'height': 600,
                'maximized': False
                }
            }

        # Load settings
        if os.access('%s/settings.cfg' % self.al.HOME, os.F_OK | os.W_OK):
            self._load_settings()

        if self.settings['username'] is None or self.settings['password'] is None:
            self.user_verified, self.block_access = False, True

        self.anime = {
            # Tab number -> watched status
            'status': (
                'watching',
                'completed',
                'on-hold',
                'dropped',
                'plan to watch'
                ),

            # Watched status -> tab number
            'rstatus': {
                'watching':      0,
                'completed':     1,
                'on-hold':       2,
                'dropped':       3,
                'plan to watch': 4
                },

            # Color status
            'cstatus': {
                'finished airing':  gtk.gdk.color_parse('#50ce18'), # Green
                'currently airing': gtk.gdk.color_parse('#1173e2'), # Bright/Light blue
                'not yet aired':    gtk.gdk.color_parse('#e20d0d'), # Red
				'unknown':          gtk.gdk.color_parse('#afafaf')  # Grey
                }
            }

        # API settings
        self.api = {
            'host': 'mal-api.com',
            'user_agent': '%s:%s' % (self.al.name, self.al.version)
            }

        # Events
        self.al.signal.connect('al-shutdown-lvl2', self._save_settings)

    def _save_settings(self, widget=None):
        # Private. Save a pickled, base64 encoded version of self.settings in settings.cfg.

        with open(self.al.HOME + '/settings.cfg', 'wb') as f:
            f.write(base64.b64encode(cPickle.dumps((self.user_verified, self.settings), cPickle.HIGHEST_PROTOCOL)))

    def _load_settings(self):
        # Private. Load contents from settings.cfg, base64 decode, unpickle and assign it to self.settings.

        with open(self.al.HOME + '/settings.cfg', 'rb') as f:
            self.user_verified, self.settings = cPickle.loads(base64.b64decode(f.read()))
