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
        self.buttons = {}
        self.buttons['refresh'] = gtk.ToolButton(gtk.STOCK_REFRESH)
        self.buttons['save'] = gtk.ToolButton(gtk.STOCK_SAVE)
        self.buttons['anime'] = gtk.ToolButton(gtk.STOCK_INFO)
        self.buttons['search'] = gtk.ToolButton(gtk.STOCK_FIND)
        self.buttons['prefs'] = gtk.ToolButton(gtk.STOCK_PREFERENCES)
        self.buttons['about'] = gtk.ToolButton(gtk.STOCK_ABOUT)
        self.buttons['quit'] = gtk.ToolButton(gtk.STOCK_QUIT)

        # Insert in toolbar
        self.insert(self.buttons['refresh'], 0)
        self.insert(self.buttons['save'], 1)
        self.insert(gtk.SeparatorToolItem(), 2)
        self.insert(self.buttons['anime'], 3)
        self.insert(self.buttons['search'], 4)
        self.insert(gtk.SeparatorToolItem(), 5)
        self.insert(self.buttons['prefs'], 6)
        self.insert(gtk.SeparatorToolItem(), 7)
        self.insert(self.buttons['about'], 8)
        self.insert(self.buttons['quit'], 9)

        # Events
        self.buttons['refresh'].connect('clicked', self.__on_refresh)
        self.buttons['save'].connect('clicked', self.__on_save)
        self.buttons['anime'].connect('clicked', self.__on_anime)
        self.buttons['search'].connect('clicked', self.__on_search)
        self.buttons['prefs'].connect('clicked', self.__on_prefs)
        self.buttons['about'].connect('clicked', self.__on_about)
        self.buttons['quit'].connect('clicked', self.al.quit)

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

