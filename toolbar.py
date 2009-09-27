#!/usr/bin/python

# =============================================================================
# toolbar.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import thread

import gtk

from lib.dialogs import about_dialog
from lib import utils

class Toolbar(gtk.Toolbar):

    def __init__(self, al):

        self.al = al
        gtk.Toolbar.__init__(self)
        self.set_style(gtk.TOOLBAR_ICONS)

        # Buttons
        self.buttons = {}
        self.__generate_buttons(self, self.buttons, (
            ('refresh', {
                'stock': gtk.STOCK_REFRESH,
                'event': ('clicked', self.__on_refresh),
                'tooltip': 'Refresh anime list'
                }),
            ('save', {
                'stock': gtk.STOCK_SAVE,
                'event': ('clicked', self.__on_save),
                'tooltip': 'Save anime list to cache'
                }),
            'separator',
            ('anime', {
                'icon': './pixmaps/monitor.png',
                'event': ('clicked', self.__on_anime),
                'tooltip': 'Go to your anime list'
                }),
            ('search', {
                'stock': gtk.STOCK_FIND,
                'event': ('clicked', self.__on_search),
                'tooltip': 'Go to the search section'
                }),
            'separator',
            ('preferences', {
                'stock': gtk.STOCK_PREFERENCES,
                'event': ('clicked', self.__on_prefs),
                'tooltip': 'Show the preferences dialog'
                }),
            'separator',
            ('about', {
                'stock': gtk.STOCK_ABOUT,
                'event': ('clicked', self.__on_about),
                'tooltip': 'Show about dialog'
                }),
            ('quit', {
                'stock': gtk.STOCK_QUIT,
                'event': ('clicked', self.al.quit),
                'tooltip': 'Quit'
                })
            ))

        # Events
        self.al.signal.connect('al-user-set', self.__enable_control)
        self.al.signal.connect('al-no-user-set', self.__disable_control)
        self.al.signal.connect('al-init-done', self.__init_done)

    # Misc functions ----------------------------------------------------------

    def __enable_control(self, widget=None):
        "Enable buttons when a user has been set."

        if self.al.current_section == 1:
            self.buttons['refresh'].set_sensitive(True)
            self.buttons['save'].set_sensitive(True)
            self.buttons['anime'].set_sensitive(False)

        if self.al.current_section == 2:
            self.buttons['search'].set_sensitive(False)

    def __disable_control(self, widget=None):
        "Disable buttons when no user has been set."

        self.buttons['refresh'].set_sensitive(False)
        self.buttons['save'].set_sensitive(False)
        self.buttons['anime'].set_sensitive(False)
        self.buttons['search'].set_sensitive(False)

    def __init_done(self, widget=None):

        # Disable anime button
        self.buttons['anime'].set_sensitive(False)

    def __generate_buttons(self, toolbar, buttons, data):
        "Generate the buttons for a toolbar."

        for i, v in enumerate(data):

            if v == 'separator':
                toolbar.insert(gtk.SeparatorToolItem(), i)
                continue

            if 'stock' in v[1]:
                toolbar.buttons[v[0]] = gtk.ToolButton(v[1]['stock'])
            else:
                toolbar.buttons[v[0]] = gtk.ToolButton()

            if 'icon' in v[1]:
                image = gtk.Image()
                image.set_from_icon_set(gtk.IconSet(gtk.gdk.pixbuf_new_from_file(v[1]['icon'])), gtk.ICON_SIZE_SMALL_TOOLBAR)
                toolbar.buttons[v[0]].set_icon_widget(image)

            toolbar.buttons[v[0]].connect(v[1]['event'][0], v[1]['event'][1])
            toolbar.buttons[v[0]].set_tooltip_text(v[1]['tooltip'])

            toolbar.insert(toolbar.buttons[v[0]], i)


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
        about_dialog(
            self.al.name,
            self.al.version,
            'Copyright (c) 2009 Frank Smit',
            'MyAnimeList.net anime list manager + some extra stuff.',
            'http://61924.nl',
            utils.get_image('./pixmaps/animelist_logo_256.png')
            )
