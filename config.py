#!/usr/bin/python

# =============================================================================
# config.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import ConfigParser

class Config():
    def __init__(self, al):

        self.al = al

        # Load preferences file
        config = ConfigParser.SafeConfigParser()
        config.read([self.al.HOME + '/preferences.cfg',])

        self.lists = {
            1: 'Watching',
            2: 'Completed',
            3: 'On-hold',
            4: 'Dropped',
            6: 'Plan to watch'
            }

        self.tab_numbers = {
            0: 1,
            1: 2,
            2: 3,
            3: 4,
            4: 6
            }

        self.types = {
            1: 'TV',
            2: 'OVA',
            3: 'Movie',
            4: 'Special',
            5: 'ONA',
            6: 'Music'
            }

        self.user = {
            'name':     config.get('user', 'name'),
            'password': config.get('user', 'password')
            }

        self.prefs = {
            'startup_refresh': False
            }

        self.mal = {
            'host': 'myanimelist.net'
            }
