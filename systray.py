#!/usr/bin/python

# =============================================================================
# systray.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os
import sys

import gtk

from lib import utils

class Systray(gtk.StatusIcon):

    def __init__(self, al):

        self.al = al
        gtk.StatusIcon.__init__(self)

        self.set_from_pixbuf(utils.get_icon('./pixmaps/animelist_logo_32.png'))
        self.connect('activate', self.__activate_icon)
        self.set_visible(True)

    #
    #  System tray icon actions
    #
    def __activate_icon(self, widget, data=None):

        if self.al.window.get_property('visible'):
            self.al.window.hide()
        else:
            self.al.window.move(self.al.window._position[0], self.al.window._position[1])
            self.al.window.show()
            self.al.window.present()
