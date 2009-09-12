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

        self.already_in_list = []
        self.fonts = (pango.FontDescription('normal'), pango.FontDescription('bold'))

        # Search bar
        self.search_entry = gtk.Entry()
        self.search_button = gtk.Button('Search')
        self.search_button.set_size_request(120, -1)

        searchbar = gtk.HBox(False, 0)
        searchbar.pack_start(self.search_entry, expand=True, fill=True, padding=5)
        searchbar.pack_start(self.search_button, expand=False, fill=False, padding=5)

        # Menu
        self.menu = gtk.Menu()
        self.menu.add_to = {}

        self.menu.details = gtk.MenuItem('Details')
        self.menu.add = gtk.MenuItem('Add to')
        self.menu.add_submenu = gtk.Menu()
        self.menu.add.set_submenu(self.menu.add_submenu)

        self.menu.append(self.menu.details)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.menu.add)

        for k, v in enumerate(self.al.config.status):
            self.menu.add_to[k] = gtk.MenuItem(v.capitalize())
            self.menu.add_to[k].connect('activate', self.__menu_add_anime, k)
            self.menu.add_submenu.append(self.menu.add_to[k])

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

        self.treeview.connect('button-press-event', self.__show_menu)

        # Create scrollbox
        frame = gtk.ScrolledWindow()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        frame.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Pack it together
        frame.add(self.treeview)
        self.pack_start(searchbar, expand=False, fill=False, padding=5)
        self.pack_end(frame, expand=True, fill=True)

        self.menu.show_all()

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
    #  Displays the main popup menu on a button-press-event
    #  with options for the selected row in the list.
    #
    def __show_menu(self, treeview, event):

        if event.button != 3:  # Only on right click
            return False

        selection = self.treeview.get_selection()
        path = selection.get_selected_rows()[1][0][0]
        anime_id = int(self.liststore[path][0])

        # Disable "Add to" on anime that are already i the list. Or should it be hidden?
        if int(anime_id) in self.already_in_list:
            self.menu.add.set_sensitive(False)
        else:
            self.menu.add.set_sensitive(True)

        self.menu.popup(None, None, None, 3, event.time)

    #
    #  Wrapper method for move()
    #
    def __menu_add_anime(self, menuitem, dest_list):

        selection = self.treeview.get_selection()
        anime_id = int(self.liststore[selection.get_selected_rows()[1][0][0]][0])

        params = {
            'id':                 self.data[anime_id]['id'],
            'title':              self.data[anime_id]['title'],
            'type':               self.data[anime_id]['type'],             # TV, Movie, OVA, ONA, Special, Music
            'episodes':           self.data[anime_id]['episodes'],
            'status':             self.data[anime_id]['status'],           # finished airing, currently airing, not yet aired
            'watched_status':     self.al.config.status[dest_list],
            'watched_episodes':   '0',
            'score':              '0'
            }

        # Show a dialog when an anime id added to "wacthing", "on-hold", "dropped" or "completed"
        if dest_list in (0, 1, 2, 3):

            # Fields
            episodes_entry = gtk.Entry()
            score_entry = gtk.SpinButton(gtk.Adjustment(0, 0, 10, 1))

            # Main table
            table = gtk.Table(2, 2)
            table.set_row_spacings(10)
            table.set_col_spacings(10)

            table.attach(gtk.Label('Episodes'), 0, 1, 0, 1)
            table.attach(gtk.Label('Score'), 0, 1, 1, 2)
            table.attach(episodes_entry, 1, 2, 0, 1)
            table.attach(score_entry, 1, 2, 1, 2)

            # Boxes for padding
            hbox = gtk.HBox()
            hbox.pack_start(table, False, True, 5)
            hbox.show_all()

            # Dialog flags and buttons
            flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
            buttons = (
                gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
                )

            if dest_list == 1:
                episodes_entry.set_text(str(params['episodes']))
                score_entry.grab_focus()

            # Create dialog
            dialog = gtk.Dialog('Add anime', self.al.window, flags, buttons)
            dialog.set_default_response(gtk.RESPONSE_ACCEPT)
            dialog.vbox.pack_start(hbox, False, True, 5)

            if dialog.run() == gtk.RESPONSE_ACCEPT:

                my_episodes = episodes_entry.get_text()
                my_score = score_entry.get_text()

                try:
                    params['watched_episodes'] = str(int(my_episodes))
                except ValueError:
                    pass

                try:
                    my_score = int(my_score)

                    if my_score  >= 0 or my_score <= 10:
                        params['score'] = str(my_score)
                except ValueError:
                    pass

                dialog.destroy()
            else:
                dialog.destroy()
                return None

        self.al.anime.add(params)

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
    #  Send request and fill the list
    #
    def __process_search(self, query):

        gtk.gdk.threads_enter()
        self.search_entry.set_sensitive(False)
        self.search_button.set_sensitive(False)
        self.al.statusbar.update('Searching...')
        gtk.gdk.threads_leave()

        self.liststore.clear()
        self.data = {}
        self.already_in_list = []

        results = self.mal.search(query)
        if results == False:
            gtk.gdk.threads_enter()
            self.al.statusbar.update('Search failed. Please try again later.')
            self.search_entry.set_sensitive(True)
            self.search_button.set_sensitive(True)
            self.search_entry.grab_focus()
            gtk.gdk.threads_leave()
            return False

        # Fill lists
        self.data = results

        gtk.gdk.threads_enter()

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

        gtk.gdk.threads_leave()

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

            try:
                self.already_in_list.index(anime_id)
            except ValueError:
                self.already_in_list.append(anime_id)
        else:
            cell.set_property('font-desc', self.fonts[0])

            try:
                self.already_in_list.pop(self.already_in_list.index(anime_id))
            except ValueError:
                pass

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
