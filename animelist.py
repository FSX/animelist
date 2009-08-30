#!/usr/bin/python

# =============================================================================
# animelist.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os

import gtk
import gobject

import config
import toolbar
import myanimelist
import lists
from modules.utils import cache_data

gtk.gdk.threads_init()

class AnimeList():
    HOME = os.path.expanduser('~/.animelist')
    app_name = 'AnimeList'
    app_version = '0.1-dev'
    tasks = []
    position = (0, 0)

    def __init__(self):

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(800, 600)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_title('AnimeList')
        self.window.set_icon(self.get_icon('./pixmaps/animelist_logo_32.png'))

        self.statusbar = gtk.Statusbar()
        self.statusbar_message_id = None

        # Classes
        self.config = config.Config(self)
        self.toolbar = toolbar.Toolbar(self)
        self.mal = myanimelist.Mal(self)
        self.lists = lists.Lists(self)

        # Only load systray module when the system is enabled
        if 'systray' in self.config.settings and self.config.settings['systray'] == True:
            import systray
            self.systray = systray.Systray(self)

        # Put everything together
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(self.toolbar.bar, False, False, 0)
        vbox.pack_start(self.lists.tabs, True, True, 0)
        vbox.pack_end(self.statusbar, False, False, 0)

        # Events
        self.window.connect('configure-event', self._store_position)
        self.window.connect('destroy', self.quit)

        # Create settings folder in home directory
        if not os.access(self.HOME, os.F_OK | os.W_OK):
            os.mkdir(self.HOME)

        # Show everything
        self.window.add(vbox)
        self.window.show_all()

        # Show preferences window when no user has been defined
        if self.config.no_user_defined == True:
            self.config.preferences_dialog()

        gtk.main()

    #
    #  Set/Update/Change statusbar text
    #
    def update_statusbar(self, text):

        if not self.statusbar_message_id is None:
            self.statusbar.remove(0, self.statusbar_message_id)

        self.statusbar_message_id = self.statusbar.push(0, text)

    #
    #  Clear statusbar
    #
    def clear_statusbar(self, remove_timeout=None):

        if not self.statusbar_message_id is None:
            if not remove_timeout is None:
                gobject.timeout_add(remove_timeout, self.statusbar.remove, 0,
                    self.statusbar_message_id)
            else:
                self.statusbar.remove(0, self.statusbar_message_id)

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
