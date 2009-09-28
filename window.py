#!/usr/bin/python

# =============================================================================
# animelist.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gtk

from lib import utils

class Window(gtk.Window):

    def __init__(self, al):

        self.al = al
        gtk.Window.__init__(self)

        # Create window
        #self.set_position(gtk.WIN_POS_CENTER)
        self.set_title(self.al.name)
        self.set_icon(utils.get_image('./pixmaps/animelist_logo_32.png'))
        self._position = (0, 0) # Stores the position of the window. Starts with an
                                # underscore, because 'position' is already taken.

        self.move(self.al.config.settings['position']['x'], self.al.config.settings['position']['x'])
        self.set_default_size(self.al.config.settings['position']['width'], self.al.config.settings['position']['height'])

        # Events
        self.connect('configure-event', self.__store_position)
        self.connect('destroy', self.al.quit)

    def __store_position(self, event, position):
        "Store the position of the window when it's moved or resized."

        self.al.config.settings['position']['x'] = position.x
        self.al.config.settings['position']['y'] = position.y

        self.al.config.settings['position']['width'] = position.width
        self.al.config.settings['position']['height'] = position.height

        self._position = (position.x, position.y)
