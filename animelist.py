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
import widgets
from lib.pygtkhelpers import gthreads
from lib.myanimelist import MAL
from plugin import PluginSys

gobject.threads_init()

class AnimeList():

    def __init__(self):

        # Set some variables
        self.HOME = os.path.expanduser('~/.animelist')
        self.name = 'AnimeList'
        self.version = '0.2-dev'
        self._position = (0, 0)
        self.path = sys.path[0]

        # Initiate modules
        self.signal = signals.Signals()
        self.config = config.Config(self)

        self.mal = MAL((
            self.config.settings['username'],
            self.config.settings['password'],
            self.config.api['host'],
            self.config.api['user_agent']
            ))

        # Load GUI
        self.builder = gtk.Builder()
        self.builder.add_from_file('%s/animelist.ui' % self.path)

        # Main window widgets
        self.gui = {
            'window': self.builder.get_object('main_window'),
            'toolbar': widgets.ToolBar(self, self.builder.get_object('mw_toolbar')),
            'menubar': self.builder.get_object('mw_menubar'),

            'menu_quit': self.builder.get_object('mw_imsi_quit'),
            'menu_settings': self.builder.get_object('mw_ismi_settings'),
            'menu_about': self.builder.get_object('mw_ismi_about'),

            'box': self.builder.get_object('mw_box'),
            'statusbar': widgets.Statusbar(self, self.builder.get_object('mw_statusbar')),
            'systray': self.builder.get_object('statusicon')
            }

        # Load plugins
        self.pluginsys = PluginSys(self, {'plugin_path': '%s/plugins/' % self.path,
            'plugins': ['anime', 'search', 'media', 'torrents']})
        self.plugins = self.pluginsys._instances

        # Set window dimensions and position
        if self.config.settings['window']['maximized'] == True:
            self.gui['window'].maximize()

        if self.config.settings['window']['x'] is not None:
            self.gui['window'].move(
                self.config.settings['window']['x'],
                self.config.settings['window']['y'])
        else:
            self.gui['window'].set_position(gtk.WIN_POS_CENTER)

        self.gui['window'].set_default_size(
            self.config.settings['window']['width'],
            self.config.settings['window']['height'])

        self.gui['window'].show_all()

        # Set up toolbar
        self.gui['toolbar'].set_section(0)

        # Create settings folder in home directory
        if not os.access(self.HOME, os.F_OK | os.W_OK):
            os.mkdir(self.HOME)

        # Events
        self.gui['menu_settings'].connect('activate', self.__menu_settings)
        self.gui['menu_about'].connect('activate', self.__menu_about)
        self.gui['menu_quit'].connect('activate', self.quit)

        self.signal.connect('al-shutdown-lvl1', self.__mw_set_position_settings)
        self.signal.connect('al-user-changed', self.verify_user)
        self.gui['window'].connect('window-state-event', self.__mw_state_changed)
        self.gui['window'].connect('configure-event', self.__mw_store_position)
        self.gui['window'].connect('destroy', self.quit)
        self.gui['systray'].connect('activate', self.__st_activate_icon)

        # Emit signal when all the stuff is ready
        self.signal.emit('al-init-done')

    def __menu_about(self, widget):
        widgets.AboutDialog(self)

    def __menu_settings(self, widget):
        widgets.SettingsDialog(self)

    def __mw_set_position_settings(self, widget):
        "Save the position and the dimensions of the window in the settings."

        # Only save the position and dimensions when the window is not maximized
        if self.config.settings['window']['maximized'] == False:
            self.config.settings['window']['x'] = self._position[0]
            self.config.settings['window']['y'] = self._position[1]
            (self.config.settings['window']['width'], self.config.settings['window']['height']) = self.gui['window'].get_size()

    def __mw_state_changed(self, widget, event):
        """A callback connected to the window's window-state-event signal. This
        is used to keep track of whether the window is maximized or not."""

        if event.new_window_state == gtk.gdk.WINDOW_STATE_MAXIMIZED:
            self.config.settings['window']['maximized'] = True
        else:
            self.config.settings['window']['maximized'] = False

    def __mw_store_position(self, event, position):
        "Store the position of the window when it's moved or resized."

        self._position = (position.x, position.y)

    def __st_activate_icon(self, widget):
        "Hide and show the main window."

        if self.gui['window'].get_property('visible'):
            self.gui['window'].hide()
        else:
            self.gui['window'].move(self._position[0], self._position[1])
            self.gui['window'].show()
            self.gui['window'].present()

    def block_access(self):

        self.config.block_access = True
        self.gui['toolbar'].set_sensitive(False)
        self.gui['box'].set_sensitive(False)

    def unblock_access(self):

        self.config.block_access = False
        self.gui['toolbar'].set_sensitive(True)
        self.gui['box'].set_sensitive(True)

    def verify_user(self, widget=None):
        "Verify current user. Block the application when the user is invalid."

        def request():
            return self.mal.verify_user()

        def callback(result):

            if result == True:
                self.signal.emit('al-user-verified')
                self.unblock_access()

                self.config.user_verified = True

                self.gui['statusbar'].update('User details are valid')
                self.gui['statusbar'].clear(2000)
            else:
                self.config.user_verified = False
                self.gui['statusbar'].update('User details are invalid. Please check your user details')

        self.block_access()
        self.gui['statusbar'].update('Verifying user details...')

        self.mal = MAL((
            self.config.settings['username'],
            self.config.settings['password'],
            self.config.api['host'],
            self.config.api['user_agent']
            ))

        t = gthreads.AsyncTask(request, callback)
        t.start()

    def quit(self, widget=None):
        "Terminates the application cleanly."

        self.signal.emit('al-shutdown-lvl1')
        self.signal.emit('al-shutdown-lvl2')
        gtk.main_quit()

if __name__ == '__main__':
    AnimeList()
    gtk.main()
