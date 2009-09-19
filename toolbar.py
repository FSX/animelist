#!/usr/bin/python

# =============================================================================
# toolbar.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import thread

import gtk

from lib import utils

class Toolbar(gtk.Toolbar):

    def __init__(self, al):

        self.al = al
        gtk.Toolbar.__init__(self)
        self.set_style(gtk.TOOLBAR_ICONS)

        # Buttons
        self.__generate_buttons([
            ('refresh', {
                'stock': gtk.STOCK_REFRESH,
                'event': self.__on_refresh,
                'tooltip': 'Refresh anime list'
                }),
            ('save', {
                'stock': gtk.STOCK_SAVE,
                'event': self.__on_save,
                'tooltip': 'Save anime list to cache'
                }),
            ('separator', None),
            ('anime', {
                'stock': gtk.STOCK_INFO,
                'event': self.__on_anime,
                'tooltip': 'Go to your anime list'
                }),
            ('search', {
                'stock': gtk.STOCK_FIND,
                'event': self.__on_search,
                'tooltip': 'Go to the search section'
                }),
            ('separator', None),
            ('preferences', {
                'stock': gtk.STOCK_PREFERENCES,
                'event': self.__on_prefs,
                'tooltip': 'Show the preferences dialog'
                }),
            ('separator', None),
            ('about', {
                'stock': gtk.STOCK_ABOUT,
                'event': self.__on_about,
                'tooltip': 'Show about dialog'
                }),
            ('quit', {
                'stock': gtk.STOCK_QUIT,
                'event': self.al.quit,
                'tooltip': 'Quit'
                })
            ])

        # Events
        self.al.signal.connect('al-user-set', self.__enable_control)
        self.al.signal.connect('al-no-user-set', self.__disable_control)
        self.al.signal.connect('al-gui-done', self.__gui_done)

    # Misc functions ----------------------------------------------------------

    def __enable_control(self, widget=None):
        "Enable buttons when a user has been set."

        self.buttons['refresh'].set_sensitive(True)
        self.buttons['save'].set_sensitive(True)
        self.buttons['anime'].set_sensitive(True)
        self.buttons['search'].set_sensitive(True)

    def __disable_control(self, widget=None):
        "Disable buttons when no user has been set."

        self.buttons['refresh'].set_sensitive(False)
        self.buttons['save'].set_sensitive(False)
        self.buttons['anime'].set_sensitive(False)
        self.buttons['search'].set_sensitive(False)

    def __gui_done(self, widget=None):

        # Disable anime button
        self.buttons['anime'].set_sensitive(False)

    def __generate_buttons(self, buttons):
        "Generate the buttons for a toolbar."

        self.buttons = {}

        for i, v in enumerate(buttons):

            if v[0] != 'separator':
                self.buttons[v[0]] = gtk.ToolButton(v[1]['stock'])
                self.buttons[v[0]].connect('clicked', v[1]['event'])
                self.buttons[v[0]].set_tooltip_text(v[1]['tooltip'])

                self.insert(self.buttons[v[0]], i)
            else:
                self.insert(gtk.SeparatorToolItem(), i)

    # Widget callbacks --------------------------------------------------------

    def __on_refresh(self, widget):
        self.al.anime.refresh()

    def __on_save(self, widget):
        self.al.anime.save()

    def __on_prefs(self, widget):
        self.al.config.preferences_dialog()

    def __on_anime(self, widget):
        self.buttons['refresh'].set_sensitive(True)
        self.buttons['save'].set_sensitive(True)
        self.buttons['search'].set_sensitive(True)
        self.buttons['anime'].set_sensitive(False)
        self.al.switch_section(1)

    def __on_search(self, widget):
        self.buttons['anime'].set_sensitive(True)
        self.buttons['refresh'].set_sensitive(False)
        self.buttons['save'].set_sensitive(False)
        self.buttons['search'].set_sensitive(False)
        self.al.switch_section(2)

    def __on_about(self, widget):
        about = gtk.AboutDialog()
        about.set_program_name(self.al.name)
        about.set_version(self.al.version)
        about.set_copyright('Copyright (c) 2009 Frank Smit')
        about.set_comments('MyAnimeList.net anime list manager + some extra stuff.')
        about.set_website('http://61924.nl')
        about.set_logo(utils.get_icon('./pixmaps/animelist_logo_256.png'))
        about.run()
        about.destroy()

