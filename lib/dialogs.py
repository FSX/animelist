#!/usr/bin/python

# =============================================================================
# lib/dialogs.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import webbrowser

import gtk

def about_dialog(name, version, copyright, comments, website, icon):
    "Shows an about dialog."

    about = gtk.AboutDialog()
    about.set_program_name(name)
    about.set_version(version)
    about.set_copyright(copyright)
    about.set_comments(comments)
    about.set_website(website)
    about.set_logo(icon)
    about.run()
    about.destroy()

class PreferencesDialog(gtk.Dialog):

    def __init__(self, window, objects):

        # Dialog flags and buttons
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
            gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
            )

        gtk.Dialog.__init__(self, 'Preferences', window, flags, buttons)
        self.set_default_response(gtk.RESPONSE_ACCEPT)

        # Table
        table = gtk.Table(len(objects), 1)
        table.set_border_width(5)
        table.set_row_spacings(10)

        for i, obj in enumerate(objects):
            table.attach(obj, 0, 1, i, i+1)

        table.show_all()

        self.vbox.pack_start(table, False, True)

class DetailsDialog(gtk.Builder):

    def __init__(self):

        gtk.Builder.__init__(self)
        self.add_from_file('./ui/details.ui')

        self.mal_url = None
        self.widgets = {
            'window': self.get_object('window'),
            'image': self.get_object('image'),
            'title': self.get_object('title'),
            'synopsis': self.get_object('synopsis'),
            'information': self.get_object('information'),
            'statistics': self.get_object('statistics'),

            'box_other_titles': self.get_object('vbox5'),
            'other_titles': self.get_object('other_titles'),

            'box_related': self.get_object('vbox6'),
            'related': self.get_object('related'),

            'mal_button': self.get_object('mal_button')
            }

        self.widgets['window'].connect('key-release-event', self.__handle_key)
        self.widgets['mal_button'].connect('clicked', self.__on_click)

    def __handle_key(self, widget, event):

        string, state = event.string, event.state
        keyname =  gtk.gdk.keyval_name(event.keyval)

        if keyname == 'Escape':
            self.widgets['window'].destroy()

    def __on_click(self, button):

        if self.mal_url is None:
            return

        webbrowser.open(self.mal_url)
