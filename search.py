#!/usr/bin/python

# =============================================================================
# search.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os
import thread

import gtk

class Search():
    def __init__(self, al):

        self.al = al

        # Search bar
        search_entry = gtk.Entry()
        search_button = gtk.Button('Search')
        search_button.set_size_request(120, 30)

        searchbar = gtk.HBox(False, 0)
        searchbar.pack_start(search_entry, expand=True, fill=True, padding=5)
        searchbar.pack_end(search_button, expand=False, fill=False, padding=5)

        # Search results list
        self.liststore = gtk.ListStore(str, str, str, str, str)

        self.treeview = gtk.TreeView(self.liststore)
        self.treeview.set_rules_hint(True)
        self.treeview.set_search_column(1)
        self.treeview.set_tooltip_column(1)
        self.treeview.columns_autosize()

        self.create_columns(self.treeview)

        # Events
        search_button.connect('clicked', self._on_search, search_entry)

        # Pack it together
        self.box = gtk.VBox(False, 0)
        self.box.pack_start(searchbar, expand=False, fill=False, padding=5)
        self.box.pack_end(self.treeview, expand=True, fill=True)

    #
    #  Get text from text field and search
    #
    def _on_search(self, button, query):
        thread.start_new_thread(self._process_search, (query.get_text(),))
        #self._process_search(query.get_text())

    def _process_search(self, query):

        self.al.sb.update('Searching...')

        results = self.al.mal.search_anime(query)
        self.liststore.clear()

        # Fill list Ghost in the shell
        if type(results) == type({}) and len(results) > 0:
            for k, v in results.iteritems():
                self.liststore.append((
                    v[0], # Anime ID (hidden)
                    v[1], # Title
                    v[2], # Type
                    v[3], # Episodes
                    v[4]  # Score
                    ))
        else:
            self.al.sb.update('No results found')

        self.al.sb.clear(1000)

    #
    #  Create columns
    #
    def create_columns(self, treeview):

        # Anime ID
        column = gtk.TreeViewColumn(None, None)
        column.set_visible(False)
        treeview.append_column(column)

        # Title
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Title', renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_expand(True)
        treeview.append_column(column)

        # Type (TV, OVA ...)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Type', renderer, text=2)
        column.set_sort_column_id(2)
        treeview.append_column(column)

        # Episodes
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Episodes', renderer, text=3)
        column.set_sort_column_id(3)
        treeview.append_column(column)

        # Score
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Score', renderer, text=4)
        column.set_sort_column_id(4)
        treeview.append_column(column)
