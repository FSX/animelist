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
import myanimelist
import lists
import search
from modules.utils import cache_data

gtk.gdk.threads_init()

class AnimeList():
    HOME = os.path.expanduser('~/.animelist')
    app_name = 'AnimeList'
    app_version = '0.1-dev'
    tasks = []
    position = (0, 0)
    current_view = 1

    def __init__(self):

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(800, 600)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_title('AnimeList')
        self.window.set_icon(self.get_icon('./pixmaps/animelist_logo_32.png'))

        # Classes
        self.config = config.Config(self)
        self.sb = statusbar.Statusbar(self)
        self.toolbar = toolbar.Toolbar(self)
        self.mal = myanimelist.Mal(self)
        self.lists = lists.Lists(self)
        self.search = search.Search(self)

        # Only load systray module when the system is enabled
        if 'systray' in self.config.settings and self.config.settings['systray'] == True:
            import systray
            self.systray = systray.Systray(self)

        # Put everything together
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(self.toolbar.bar, False, False, 0)
        vbox.pack_start(self.lists.tabs, True, True, 0)
        vbox.pack_start(self.search.box, True, True, 0)
        vbox.pack_end(self.sb.statusbar, False, False, 0)

        # Events
        self.window.connect('configure-event', self._store_position)
        self.window.connect('destroy', self.quit)

        # Create settings folder in home directory
        if not os.access(self.HOME, os.F_OK | os.W_OK):
            os.mkdir(self.HOME)

        # Show everything
        self.window.add(vbox)
        self.window.show_all()

        # Hide search
        #self.lists.tabs.hide()
        self.search.box.hide()

        # Show preferences window when no user has been defined
        if self.config.no_user_defined == True:
            self.config.preferences_dialog()

        gtk.main()

    #
    #  Switch view (list to search or search to list)\
    #
    def switch_view(self, view):

        if view in (1, 2):
            if view == 1 and self.current_view == 2:
                self.search.box.hide()
                self.lists.tabs.show()
            elif view == 2 and self.current_view == 1:
                self.lists.tabs.hide()
                self.search.box.show()

            self.current_view = view

    #
    #  Returns a gtk.gdk.Pixbuf
    #
    def get_icon(self, icon):

        if os.access(icon, os.F_OK):
            return gtk.gdk.pixbuf_new_from_file(icon)

        return None

    #
    #  Store the position of the window when it's moved or resized
    #
    def _store_position(self, event, position):
        self.position = (position.x, position.y)

    #
    #  Terminates the application cleanly.
    #
    def quit(self, widget, data=None):

        if self.config.no_user_defined == False:
            cache_data(self.HOME + '/' + self.config.settings['username'] + \
                '_animelist.cpickle', self.lists.anime_data)

        gtk.main_quit()

if __name__ == '__main__':
    AnimeList()
