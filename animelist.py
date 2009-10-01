#!/usr/bin/python

# =============================================================================
# animelist.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os
import sys

import pygtk
pygtk.require('2.0')
import gobject
import gtk

import signals
import config
import gui
from plugins import anime, search

gobject.threads_init()

class AnimeList():

    def __init__(self):

        # Set some variables
        self.HOME = os.path.expanduser('~/.animelist')
        self.name = 'AnimeList'
        self.version = '0.1-dev'
        self.current_section = 1
        self.handlers = []

        # Initiate modules
        self.signal = signals.Signals()
        self.config = config.Config(self)
        self.window = gui.Window(self)
        self.statusbar = gui.Statusbar(self)
        self.toolbar = gui.Toolbar(self)
        self.anime = anime.Anime(self)
        self.search = search.Search(self)

        # Only load systray module when the system is enabled
        if 'systray' in self.config.settings and self.config.settings['systray'] == True:
            self.systray = gui.Systray(self)

        # Put everything together
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(self.toolbar, False, False)
        vbox.pack_start(self.search)
        vbox.pack_start(self.anime)
        vbox.pack_end(self.statusbar, False, False)

        self.window.add(vbox)
        self.window.show_all()

        # Emit signal when all the GUI stuff is ready
        self.signal.emit('al-init-done')

        # Create settings folder in home directory
        if not os.access(self.HOME, os.F_OK | os.W_OK):
            os.mkdir(self.HOME)

        # Show preferences window when no user has been defined.
        # This is called after everything else because the preferences
        # dialog blocks.
        if self.config.no_user_defined == True:
            self.signal.emit('al-no-user-set')
            self.config.preferences_dialog()

    def switch_section(self, id):
        "Hide current section and shows the new section."

        if id in (1, 2):
            if id == 1 and self.current_section == 2:
                self.search.hide()
                self.anime.show()
            elif id == 2 and self.current_section == 1:
                self.anime.hide()
                self.search.show()

            self.current_section = id

    def quit(self, widget, data=None):
        "Terminates the application cleanly."

        self.signal.emit('al-shutdown-lvl1')
        self.signal.emit('al-shutdown-lvl2')
        gtk.main_quit()

if __name__ == '__main__':
    AnimeList()
    gtk.main()
