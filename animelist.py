#!/usr/bin/python

# =============================================================================
# animelist.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os
import sys

import gtk

import config
import statusbar
import toolbar
import systray
from sections import anime, search

gtk.gdk.threads_init()

class AnimeList():

    def __init__(self):

        # Set some variables
        self.HOME = os.path.expanduser('~/.animelist')
        self.name = 'AnimeList'
        self.version = '0.1-dev'
        self.current_section = 1
        self.shutdown_funcs = []

        # Create window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(800, 600)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_title(self.name)
        self.window.set_icon(self.get_icon('./pixmaps/animelist_logo_32.png'))
        self.window._position = (0, 0) # Stores the position of the window. Starts with an
                                       # underscore, because 'position' is already taken.

        # Initiate modules
        self.config = config.Config(self)
        self.statusbar = statusbar.Statusbar(self)
        self.toolbar = toolbar.Toolbar(self)
        self.anime = anime.Anime(self)
        self.search = search.Search(self)

        # Only load systray module when the system is enabled
        if 'systray' in self.config.settings and self.config.settings['systray'] == True:
            self.systray = systray.Systray(self)

        # Put everything together
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(self.toolbar, False, False, 0)
        vbox.pack_start(self.anime, True, True, 0)
        vbox.pack_end(self.statusbar, False, False, 0)

        self.window.add(vbox)
        self.window.show_all()

        # Events
        self.window.connect('configure-event', self.__store_position)
        self.window.connect('destroy', self.quit)

        # Show preferences window when no user has been defined
        if self.config.no_user_defined == True:
            self.config.preferences_dialog()

        # Create settings folder in home directory
        if not os.access(self.HOME, os.F_OK | os.W_OK):
            os.mkdir(self.HOME)

    #
    #  Returns a gtk.gdk.Pixbuf
    #
    def switch_section(self, id):

        if id in (1, 3):
            if id == 1 and self.current_section == 2:
                pass
            elif id == 2 and self.current_section == 3:
                pass

            self.current = name

    #
    #  Returns a gtk.gdk.Pixbuf
    #
    def get_icon(self, icon):

        if os.access(icon, os.F_OK):
            return gtk.gdk.pixbuf_new_from_file(icon)

    #
    #  Terminates the application cleanly.
    #
    def quit(self, widget, data=None):

        for f in self.shutdown_funcs:
            eval(f + '()')

        gtk.main_quit()

    #
    #  Store the position of the window when it's moved or resized
    #
    def __store_position(self, event, position):
        self.window._position = (position.x, position.y)

if __name__ == '__main__':
    AnimeList()
    gtk.main()
