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

class Systray():

    def __init__(self, al):

        self.al = al

        self.staticon = gtk.StatusIcon()
        self.staticon.set_from_pixbuf(self.al.get_icon('./pixmaps/animelist_logo_32.png'))
        self.staticon.connect('activate', self._activate_icon)
        self.staticon.set_visible(True)

    #
    #  System tray icon actions
    #
    def _activate_icon(self, widget, data=None):

        if self.al.window.get_property('visible'):
            self.al.window.hide()
        else:
            self.al.window.move(self.al.position[0], self.al.position[1])
            self.al.window.show()
            self.al.window.present()
