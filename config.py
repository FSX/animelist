#!/usr/bin/python

# =============================================================================
# config.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os
import base64
import cPickle

import gtk

from lib.dialogs import PreferencesDialog

class Config():

    def __init__(self, al):

        self.al = al
        self.no_user_defined = False

        # Set default settings
        self.settings = {
            'username': '',
            'password': '',
            'startup_refresh': True,
            'systray': True,
            'position': {
                'x': None,
                'y': None,
                'width': 800,
                'height': 600,
                'maximized': False
                }
            }

        # Load settings
        if os.access(self.al.HOME + '/settings.cfg', os.F_OK | os.W_OK):
            self.__load_settings()

        if len(self.settings['username']) < 1 and len(self.settings['password']) < 1:
            self.no_user_defined = True

        # Tab number -> watched status
        self.status = (
            'watching',
            'completed',
            'on-hold',
            'dropped',
            'plan to watch'
            )

        # Watched status -> tab number
        self.rstatus = {
            'watching':      0,
            'completed':     1,
            'on-hold':       2,
            'dropped':       3,
            'plan to watch': 4
            }

        # Color status
        self.cstatus = {
            'finished airing':  gtk.gdk.color_parse('#50ce18'), # Green
            'currently airing': gtk.gdk.color_parse('#1173e2'), # Bright/Light blue
            'not yet aired':    gtk.gdk.color_parse('#e20d0d')  # Red
            }

        # API settings
        self.api = {
            'host': 'mal-api.com',
            'user_agent': '%s:%s' % (self.al.name, self.al.version)
            }

        # Events
        self.al.signal.connect('al-shutdown-lvl2', self.__save_settings)

    def preferences_dialog(self):
        "Preferences dialog."

        # Field (entry, checknutton) objects are saved in this variable
        self.fields = {}

        # Objects (fields, text, frames) that are displayed in the prefs dialog
        objects = (
            gtk.Label('Settings marked with a * will take effect after\nthe application has been restarted.'),
            self.__generate_box(
                'User details', {
                    'username': ('Username', 'entry'),
                    'password': ('Password', 'secret_entry')}),
            self.__generate_box(
                'Options', {
                    'startup_refresh': (
                        'Sync list with MyAnimeList on startup',
                        'checkbox'),
                    'systray': (
                        'Enable system tray icon *',
                        'checkbox'),
                        })
            )

        self.prefsdialog = PreferencesDialog(self.al.window, objects)

        if self.prefsdialog.run() == gtk.RESPONSE_ACCEPT:

            tmp_settings = {}

            # Update settings in self.settings
            for field_id, widget in self.fields.iteritems():

                widget_type = widget.get_name()

                if widget_type == 'GtkEntry':
                    tmp_settings[field_id] = widget.get_text()
                elif widget_type == 'GtkCheckButton':
                    tmp_settings[field_id] = widget.get_active()

            # Check if user details are entered
            if len(tmp_settings['username']) > 0 and len(tmp_settings['password']) > 0:
                self.no_user_defined = False
                self.al.signal.emit('al-user-set')

                # Only send a signal when the user details have been changed
                if tmp_settings['username'] != self.settings['username'] and tmp_settings['password'] != self.settings['password']:
                    self.al.signal.emit('al-user-details-changed')
            else:
                self.al.signal.emit('al-no-user-set')

            for k in tmp_settings:
                self.settings[k] = tmp_settings[k]

            # Save settings to settings file
            self.__save_settings()

            # Emit signal
            self.al.signal.emit('al-pref-reset')

        self.prefsdialog.destroy()

    def __generate_box(self, name, fields):
        """Generates frames with fields in it. All field objects are saved in self.fields (dict).
           Note: only support for gtk.Entry and gtk.CheckButton at this moment."""

        frame = gtk.Frame(name)
        table = gtk.Table(2, 2)
        table.set_row_spacings(5)
        table.set_col_spacings(5)

        count = 0

        for field_id, field in fields.iteritems():

            if field[1] == 'entry' or field[1] == 'secret_entry':
                self.fields[field_id] = gtk.Entry()

                if field[1] == 'secret_entry':
                    self.fields[field_id].set_visibility(False)

                if field_id in self.settings:
                    self.fields[field_id].set_text(self.settings[field_id])

                table.attach(gtk.Label(field[0]), 0, 1, count, count+1)
                table.attach(self.fields[field_id], 1, 2, count, count+1)
            elif field[1] == 'checkbox':
                self.fields[field_id] = gtk.CheckButton(field[0])

                if field_id in self.settings and self.settings[field_id] == True:
                    self.fields[field_id].set_active(True)

                table.attach(self.fields[field_id], 0, 1, count, count+1)

            count += 1

        # Boxes for padding
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        vbox.pack_start(table, False, True, 10)
        hbox.pack_start(vbox, False, True, 10)

        frame.add(hbox)

        return frame

    def __save_settings(self, widget=None):
        "Save a pickled, base64 encoded version of self.settings in settings.cfg."

        with open(self.al.HOME + '/settings.cfg', 'wb') as f:
            f.write(base64.b64encode(cPickle.dumps(self.settings, cPickle.HIGHEST_PROTOCOL)))

    def __load_settings(self):
        "Load contents from settings.cfg, base64 decode, unpickle and assign it to self.settings."

        with open(self.al.HOME + '/settings.cfg', 'rb') as f:
            self.settings = cPickle.loads(base64.b64decode(f.read()))
