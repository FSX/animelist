# =============================================================================
# plugins/media.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gtk

from lib.plugin import BasePlugin

class Plugin(BasePlugin):

    plugin_data = {
        'name': 'media',
        'fancyname': 'Media',
        'version': '0.1',
        'description': 'Adds a media section that detects mediaplayers and auto updates the animelist.'
        }

    def __init__(self, al):
        BasePlugin.__init__(self, al)

    def _load_plugin(self):

        # Toolbar button
        self.al.gui['toolbar'].insert(self.plugin_data['fancyname'], 2)

        # GUI
        self.main_gui = gtk.Label('Media section')
        self.al.gui['box'].pack_start(self.main_gui)

    def _switch_section(self, widget, section_name):

        if section_name == self.plugin_data['fancyname']:
            self.main_gui.show()
        else:
            self.main_gui.hide()
