#!/usr/bin/python

# =============================================================================
# toolbar.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import thread

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
        refresh.connect('clicked', self._on_refresh)
        save.connect('clicked', self._on_save)
        info.connect('clicked', self._on_info)
        prefs.connect('clicked', self._on_prefs)
        about.connect('clicked', self._on_about)
        quit.connect('clicked', self.al.quit)

    def _on_refresh(self, widget):
        if self.al.config.no_user_defined == False:
            thread.start_new_thread(self.al.lists.create_rows, (True,))

    def _on_save(self, widget):

        if self.al.config.no_user_defined == False:
            self.al.sb.update('Saving data to local cache...')
            self.al.sb.clear(2000)

            from modules import utils
            utils.cache_data(self.al.HOME + '/' + self.al.config.settings['username'] + \
                '_animelist.cpickle', self.al.lists.anime_data)

    def _on_prefs(self, widget):
        self.al.config.preferences_dialog()

    def _on_info(self, widget):
        # TODO: Show a new window with information about the selected anime.
        print 'Show information/manual.'

    def _on_about(self, widget):
        about = gtk.AboutDialog()
        about.set_program_name(self.al.app_name)
        about.set_version(self.al.app_version)
        about.set_copyright('Copyright (c) 2009 Frank Smit')
        about.set_comments('MyAnimeList.net anime list manager + some extra stuff.')
        about.set_website('http://61924.nl')
        about.set_logo(self.al.get_icon('./pixmaps/animelist_logo_256.png'))
        about.run()
        about.destroy()

