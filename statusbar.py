#!/usr/bin/python

# =============================================================================
# statusbar.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gtk
import gobject

class Statusbar():

    def __init__(self, al):

        self.al = al

        self.statusbar = gtk.Statusbar()
        self.statusbar_message_id = None

    #
    #  Set/Update/Change statusbar text
    #
    def update(self, text):

        if not self.statusbar_message_id is None:
            self.statusbar.remove(0, self.statusbar_message_id)

        self.statusbar_message_id = self.statusbar.push(0, text)

    #
    #  Clear statusbar
    #
    def clear(self, remove_timeout=None):

        if not self.statusbar_message_id is None:
            if not remove_timeout is None:
                gobject.timeout_add(remove_timeout, self.statusbar.remove, 0,
                    self.statusbar_message_id)
            else:
                self.statusbar.remove(0, self.statusbar_message_id)
