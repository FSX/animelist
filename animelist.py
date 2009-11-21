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

from lib import signals
from lib import config
from lib import widgets
from lib.pygtkhelpers import gthreads
from lib.myanimelist import MAL
from lib.plugin import PluginSys

gobject.threads_init()

class AnimeList():
    """The main class which loads and starts all the necessary modules, plugins
       and all other things."""

    def __init__(self):

        # Set some variables
        self.HOME = os.path.expanduser('~/.animelist')
        self.name = 'AnimeList'
        self.version = '0.2-dev'
        self._position = (0, 0)
        self.path = sys.path[0] # This is used to load image and other resources

        # Create signals, load configuration and API
        self.signal = signals.Signals()
        self.config = config.Config(self)
        self.clipboard = gtk.Clipboard()

        self.mal = MAL((
            self.config.settings['username'],
            self.config.settings['password'],
            self.config.api['host'],
            self.config.api['user_agent']
            ))

        # Load GTK Builder (GUI) file
        self.builder = gtk.Builder()
        self.builder.add_from_file('%s/animelist.ui' % self.path)

        # Add all important widgets to a dictionary for easy access
        self.gui = {
            'window': self.builder.get_object('main_window'),
            'toolbar': widgets.ToolBar(self, self.builder.get_object('mw_toolbar')),
            'menubar': self.builder.get_object('mw_menubar'),

            'menu_quit': self.builder.get_object('mw_imsi_quit'),
            'menu_settings': self.builder.get_object('mw_ismi_settings'),
            'menu_get_help': self.builder.get_object('mw_ismi_get_help'),
            'menu_about': self.builder.get_object('mw_ismi_about'),

            'box': self.builder.get_object('mw_box'),
            'statusbar': widgets.Statusbar(self, self.builder.get_object('mw_statusbar')),
            'systray': self.builder.get_object('statusicon')
            }

        # Load plugins and send signal when all plugins are loaded
        self.pluginsys = PluginSys(self, {'plugin_path': '%s/plugins/' % self.path,
            'plugins': ['anime', 'search', 'torrents']})
        self.plugins = self.pluginsys._instances
        self.signal.emit('al-plugin-init-done')

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

        # Make all the GUI widgets visible
        self.gui['window'].show_all()

        # Accelerators for menu items
        accel_group = gtk.AccelGroup()
        self.gui['window'].add_accel_group(accel_group)

        self.gui['menu_quit'].add_accelerator('activate', accel_group, ord('Q'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        self.gui['menu_get_help'].add_accelerator('activate', accel_group, gtk.gdk.keyval_from_name('F1'), 0, gtk.ACCEL_VISIBLE)

        # Create settings folder in home directory
        if not os.access(self.HOME, os.F_OK | os.W_OK):
            os.mkdir(self.HOME)

        # Events
        self.gui['menu_quit'].connect('activate', self.quit)
        self.gui['menu_settings'].connect('activate', self.__menu_settings)
        self.gui['menu_get_help'].connect('activate', self.__menu_get_help)
        self.gui['menu_about'].connect('activate', self.__menu_about)

        self.signal.connect('al-shutdown-lvl1', self.__mw_set_position_settings)
        self.signal.connect('al-user-changed', self.verify_user)
        self.gui['window'].connect('window-state-event', self.__mw_state_changed)
        self.gui['window'].connect('configure-event', self.__mw_store_position)
        self.gui['window'].connect('destroy', self.quit)
        self.gui['systray'].connect('activate', self.__st_activate_icon)

        # Check
        if self.config.user_verified == False:
            self.block_access()
            widgets.SettingsDialog(self)

        # Emit signal when has been loaded and initiated,
        # except actions started by plugins.
        self.signal.emit('al-init-done')

    def __menu_get_help(self, widget):
        print widget # For testing

    def __menu_about(self, widget):
        "Show the 'About' dialog."

        widgets.AboutDialog(self)

    def __menu_settings(self, widget):
        "Show the settings dialog."

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
        "Block access to the GUI, except the menu."

        self.config.block_access = True
        self.gui['toolbar'].enable(False)
        self.gui['box'].set_sensitive(False)

    def unblock_access(self):
        "Unblock the access to the GUI."

        self.config.block_access = False
        self.gui['toolbar'].enable(True)
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

        # Reset API, because the user details have been changed.
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

        # There are two shutdown signals, because methods that are connected to
        # the signals are not executed in the right order.  It could be possible
        # that settings are written to the disk before the changed settings are
        # saved.  That's why lvl1 should be used to save all the settings and lvl2
        # to write everything to the disk.

        self.signal.emit('al-shutdown-lvl1')
        self.signal.emit('al-shutdown-lvl2')
        gtk.main_quit()

if __name__ == '__main__':
    AnimeList()
    gtk.main()
