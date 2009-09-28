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
        self.set_gravity(gtk.gdk.GRAVITY_NORTH_WEST)
        self.set_title(self.al.name)
        self.set_icon(utils.get_image('./pixmaps/animelist_logo_32.png'))
        self._position = (0, 0) # Stores the position of the window. Starts with an
                                # underscore, because 'position' is already taken.

        if self.al.config.settings['position']['maximized'] == True:
            self.maximize()

        if self.al.config.settings['position']['x'] is not None:
            self.move(self.al.config.settings['position']['x'], self.al.config.settings['position']['y'])
        else:
            self.set_position(gtk.WIN_POS_CENTER)

        self.set_default_size(self.al.config.settings['position']['width'], self.al.config.settings['position']['height'])

        # Events
        self.al.signal.connect('al-shutdown-lvl1', self.__set_position_settings)
        self.connect('window-state-event', self.__state_changed)
        self.connect('configure-event', self.__store_position)
        self.connect('destroy', self.al.quit)

    def __set_position_settings(self, widget):
        "Save the position and the dimensions of the window in the settings."

        # Only save the position and dimensions when the window is not maximized
        if self.al.config.settings['position']['maximized'] == False:
            self.al.config.settings['position']['x'] = self._position[0]
            self.al.config.settings['position']['y'] = self._position[1]
            (self.al.config.settings['position']['width'], self.al.config.settings['position']['height']) = self.get_size()

    def __state_changed(self, widget, event):
        """A callback connected to the window's window-state-event signal. This
        is used to keep track of whether the window is maximized or not."""

        if event.new_window_state == gtk.gdk.WINDOW_STATE_MAXIMIZED:
            self.al.config.settings['position']['maximized'] = True
        else:
            self.al.config.settings['position']['maximized'] = False

    def __store_position(self, event, position):
        "Store the position of the window when it's moved or resized."

        self._position = (position.x, position.y)
