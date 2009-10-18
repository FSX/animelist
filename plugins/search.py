#!/usr/bin/python

# =============================================================================
# plugins/search.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gtk

from plugin import BasePlugin

class Plugin(BasePlugin):

    plugin_data = {
        'name': 'search',
        'fancyname': 'Search',
        'version': '0.1',
        'description': 'Adds a anime/manga search section.'
        }

    def __init__(self, al):

        self.al = al
        self._load_plugin()

    def _load_plugin(self):

        # Toolbar button
        self.al.gui['toolbar'].insert(self.plugin_data['fancyname'], 1)

        # GUI
        self.label = gtk.Label('Search section')
        self.al.gui['box'].pack_start(self.label)

        # Events
        self.al.signal.connect('al-switch-section', self.__switch_section)

    def _unload_plugin(self):
        pass

    def __switch_section(self, widget, section_name):

        if section_name == self.plugin_data['fancyname']:
            self.label.show()
        else:
            self.label.hide()
