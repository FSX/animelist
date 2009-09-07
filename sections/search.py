#!/usr/bin/python

# =============================================================================
# sections/search.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gtk
import pango

from lib import myanimelist, utils

class Search(gtk.VBox):

    def __init__(self, al):

        self.al = al
        gtk.VBox.__init__(self)

        self.selected_path = None
        self.fonts = (pango.FontDescription('normal'), pango.FontDescription('bold'))

        # Search bar
        self.search_entry = gtk.Entry()
        self.search_button = gtk.Button('Search')
        self.search_button.set_size_request(120, -1)

        self.add_button = gtk.Button('Add')
        self.add_button.set_size_request(120, -1)
        self.add_button.set_sensitive(False)

        searchbar = gtk.HBox(False, 0)
        searchbar.pack_start(self.search_entry, expand=True, fill=True, padding=5)
        searchbar.pack_start(self.search_button, expand=False, fill=False, padding=5)

        searchbar.pack_start(gtk.VSeparator(), expand=False, fill=False, padding=5)
        searchbar.pack_start(self.add_button, expand=False, fill=False, padding=5)

        # Search results list
        self.liststore = gtk.ListStore(str, str, str, str, str, str)

        self.treeview = gtk.TreeView(self.liststore)
        self.treeview.set_rules_hint(True)
        self.treeview.set_search_column(1)
        self.treeview.set_tooltip_column(1)
        self.treeview.columns_autosize()

        self.__create_columns()

        # Events
        self.search_entry.connect('key-release-event', self.__handle_key)
        self.search_button.connect('clicked', self.__on_search)
        self.add_button.connect('clicked', self.__on_add)
        self.treeview.connect('button-release-event', self.__handle_selection)

        # Create scrollbox
        frame = gtk.ScrolledWindow()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        frame.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Pack it together
        frame.add(self.treeview)
        self.pack_start(searchbar, expand=False, fill=False, padding=5)
        self.pack_end(frame, expand=True, fill=True)

        # Set setting for the MAL api
        self.mal = myanimelist.Anime((
            self.al.config.settings['username'],
            self.al.config.settings['password'],
            self.al.config.api['host'],
            self.al.config.api['user_agent']
            ))

    #
    #  Handle key events
    #
    def __handle_key(self, widget, event):

        string, state = event.string, event.state
        keyname =  gtk.gdk.keyval_name(event.keyval)

        if keyname == 'Return':
            self.__on_search(None)

    #
    # Unselect row, if it's selected, onclick
    #
    def __handle_selection(self, treeview, event):

        if event.button != 1:  # Only on left click
            return False

        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))

        if pthinfo is not None:
            path, col, cellx, celly = pthinfo
            selection = treeview.get_selection()

            if self.selected_path == path:
                self.selected_path = None
                selection.unselect_path(path)
                self.add_button.set_sensitive(False)
            else:
                self.selected_path = path
                self.add_button.set_sensitive(True) # Activate "Add" button when a row is selected

    #
    #  Get text from text field and search
    #
    def __on_search(self, button):

        query = self.search_entry.get_text().strip()

        if len(query) < 3:
            self.al.statusbar.update('Please enter a longer search query.')
            self.search_entry.grab_focus()
            return False

        utils.sthread(self.__process_search, (query,))

    #
    #  Add selected anime/row to the list
    #
    def __on_add(self, button):

        selection = self.treeview.get_selection()
        anime_id = int(self.liststore[selection.get_selected_rows()[1][0][0]][0])

        params = {
            'id':                 self.data[anime_id]['id'],
            'title':              self.data[anime_id]['title'],
            'type':               self.data[anime_id]['type'],             # TV, Movie, OVA, ONA, Special, Music
            'episodes':           self.data[anime_id]['episodes'],
            'status':             self.data[anime_id]['status'],           # finished airing, currently airing, not yet aired
            'watched_status':     'plan to watch',
            'api_watched_status': '"plantowatch"',
            'watched_episodes':   '0',
            'score':              '0'
            }

        self.al.anime.add(params)

    #
    #  Send request and fill the list
    #
    def __process_search(self, query):

        self.search_entry.set_sensitive(False)
        self.search_button.set_sensitive(False)

        self.al.statusbar.update('Searching...')
        self.liststore.clear()
        self.data = {}

        results = self.mal.search(query)
        if results == False:
            self.al.statusbar.update('Search failed. Please try again later.')
            self.search_entry.set_sensitive(True)
            self.search_button.set_sensitive(True)
            self.search_entry.grab_focus()
            return False

        # Fill lists
        self.data = results
        for k, v in self.data.iteritems():
            self.liststore.append((
                v['id'],           # Anime ID (hidden)
                None,              # Status
                v['title'],        # Title
                v['type'],         # Type
                v['episodes'],     # Episodes
                v['members_score'] # Score
                ))

        num_results = len(results)

        if num_results > 0:
            self.al.statusbar.update('Found %d anime.' % num_results)
        else:
            self.al.statusbar.update('No anime with that name.')

        self.search_entry.set_sensitive(True)
        self.search_button.set_sensitive(True)
        self.search_entry.grab_focus()

    #
    #  Set background for status column
    #
    def __cell_status_display(self, column, cell, model, iter):

        anime_id = int(model.get_value(iter, 0))
        status = self.data[anime_id]['status']

        cell.set_property('background-gdk', self.al.config.cstatus[status])

    #
    #  The the text bold in rows (animes) that are already in your list
    #
    def __cell_title_display(self, column, cell, model, iter):

        anime_id = int(model.get_value(iter, 0))

        if anime_id in self.al.anime.data:
            cell.set_property('font-desc', self.fonts[1])
        else:
            cell.set_property('font-desc', self.fonts[0])

    #
    #  Create columns
    #
    def __create_columns(self):

        # Anime ID
        column = gtk.TreeViewColumn(None, None)
        column.set_visible(False)
        self.treeview.append_column(column)

        # Status (color)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(None, renderer, text=1)
        column.set_resizable(False)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(8)
        column.set_cell_data_func(renderer, self.__cell_status_display)
        self.treeview.append_column(column)

        # Title
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Title', renderer, text=2)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_expand(True)
        column.set_cell_data_func(renderer, self.__cell_title_display)
        self.treeview.append_column(column)

        # Type (TV, OVA ...)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Type', renderer, text=3)
        column.set_sort_column_id(3)
        self.treeview.append_column(column)

        # Episodes
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Episodes', renderer, text=4)
        column.set_sort_column_id(4)
        self.treeview.append_column(column)

        # Score
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Score', renderer, text=5)
        column.set_sort_column_id(5)
        self.treeview.append_column(column)
