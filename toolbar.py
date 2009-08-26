#!/usr/bin/python

# =============================================================================
# toolbar.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gtk

class Toolbar():
    def __init__(self, al):
        self.al = al

        self.bar = gtk.Toolbar()
        self.bar.set_style(gtk.TOOLBAR_ICONS)

        refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
        save = gtk.ToolButton(gtk.STOCK_SAVE)
        info = gtk.ToolButton(gtk.STOCK_INFO)
        find = gtk.ToolButton(gtk.STOCK_FIND)
        media = gtk.ToolButton(gtk.STOCK_MEDIA_PLAY)
        prefs = gtk.ToolButton(gtk.STOCK_PREFERENCES)
        about = gtk.ToolButton(gtk.STOCK_ABOUT)
        quit = gtk.ToolButton(gtk.STOCK_QUIT)

        self.bar.insert(refresh, 0)
        self.bar.insert(save, 1)
        self.bar.insert(gtk.SeparatorToolItem(), 2)
        self.bar.insert(info, 3)
        self.bar.insert(find, 4)
        self.bar.insert(media, 5)
        self.bar.insert(gtk.SeparatorToolItem(), 6)
        self.bar.insert(prefs, 7)
        self.bar.insert(gtk.SeparatorToolItem(), 8)
        self.bar.insert(about, 9)
        self.bar.insert(quit, 10)

        # Events
        refresh.connect('clicked', self.on_refresh)
        save.connect('clicked', self.on_save)
        info.connect('clicked', self.on_info)
        prefs.connect('clicked', self.on_prefs)
        about.connect('clicked', self.on_about)
        quit.connect('clicked', self.al.quit)

    def on_refresh(self, widget):
        self.al.lists.refresh_lists()

    def on_save(self, widget):

        self.al.update_statusbar('Saving data to local cache...')
        self.al.clear_statusbar(2000)

        from modules import utils
        utils.cache_data(self.al.HOME + '/' + self.al.config.user['name'] + \
            '_animelist.cpickle', self.al.lists.anime_data)

    def on_prefs(self, widget):
        # TODO: Show preferences window.
        print 'Show preferences window.'

    def on_info(self, widget):
        # TODO: Show a new window with information about the selected anime.
        print 'Show information/manual.'

    def on_about(self, widget):
        # TODO: Show about dialog.
        print 'Show about dialog.'
