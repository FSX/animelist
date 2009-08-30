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

class Config():
    def __init__(self, al):

        self.al = al
        self.no_user_defined = False

        # Set default settings
        self.settings = {
            'username': '',
            'password': '',
            'startup_refresh': True,
            'systray': True
            }

        # Load settings
        if os.access(self.al.HOME + '/settings.cfg', os.F_OK | os.W_OK):
            self._load_settings()

        if not ('username' in self.settings and 'password' in self.settings and\
            len(self.settings['username']) > 0 and len(self.settings['password']) > 0):
            self.no_user_defined = True

        self.lists = {
            1: 'Watching',
            2: 'Completed',
            3: 'On-hold',
            4: 'Dropped',
            6: 'Plan to watch'
            }

        self.tab_numbers = {
            0: 1,
            1: 2,
            2: 3,
            3: 4,
            4: 6
            }

        self.types = {
            1: 'TV',
            2: 'OVA',
            3: 'Movie',
            4: 'Special',
            5: 'ONA',
            6: 'Music'
            }

        self.mal = {
            'host': 'myanimelist.net'
            }

    #
    #  Preferences dialog
    #
    def preferences_dialog(self):

        self.fields = {}

        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT

        buttons = (
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
            gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
            )

        objects = (
            gtk.Label('Settings marked with a * will take effect\nwhen the application if restarted.'),
            self._generate_box(
                'User details', {
                    'username': ('Username', 'entry'),
                    'password': ('Password', 'secret_entry')}),
            self._generate_box(
                'Options', {
                    'startup_refresh': (
                        'Sync list with MyAnimeList on startup',
                        'checkbox'),
                    'systray': (
                        'Enable system tray icon *',
                        'checkbox'),
                        })
            )

        # Main table
        table = gtk.Table(len(objects), 1)
        table.set_row_spacings(10)
        table.set_col_spacings(10)

        for i, obj in enumerate(objects):
            table.attach(obj, 0, 1, i, i+1)

        # Boxes for padding
        hbox = gtk.HBox()
        hbox.pack_start(table, False, True, 5)
        hbox.show_all()

        dialog = gtk.Dialog('Preferences', self.al.window, flags, buttons)
        dialog.set_default_response(gtk.RESPONSE_ACCEPT)
        dialog.vbox.pack_start(hbox, False, True, 5)

        if dialog.run() == gtk.RESPONSE_ACCEPT:

            # Update settings in self.settings
            for field_id, widget in self.fields.iteritems():

                widget_type = widget.get_name()

                if widget_type == 'GtkEntry':
                    self.settings[field_id] = widget.get_text()
                elif widget_type == 'GtkCheckButton':
                    self.settings[field_id] = widget.get_active()

            # Save settings to settings file
            self._save_settings()

            # When user details are entered for the first time
            if self.no_user_defined == True:
                self.no_user_defined = False

        dialog.destroy()

    #
    #  Generates frames with fields in it
    #  All field objects are saved in self.fields (dict)
    #  Note: only support for gtk.Entry and gtk.CheckButton at this moment
    #
    def _generate_box(self, name, fields):

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

    #
    #  Save a piclked, base64 encoded version of self.settings in settings.cfg
    #
    def _save_settings(self):

        with open(self.al.HOME + '/settings.cfg', 'w') as f:
            f.write(base64.b64encode(cPickle.dumps(self.settings)))

    #
    #  Load contents from settings.cfg, base64 decode, unpickle and assign it to self.settings
    #
    def _load_settings(self):

        with open(self.al.HOME + '/settings.cfg', 'r') as f:
            self.settings = cPickle.loads(base64.b64decode(f.read()))
