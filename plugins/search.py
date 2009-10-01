#!/usr/bin/python

# =============================================================================
# sections/search.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os

import gtk
import pango

from lib import myanimelist, utils
from lib.dialogs import DetailsDialog
from lib.pygtkhelpers import gthreads

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

        searchbar = gtk.HBox(False, 8)
        searchbar.set_border_width(5)
        searchbar.pack_start(self.search_entry)
        searchbar.pack_start(self.search_button, False, False)

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
        self.liststore = gtk.ListStore(int, str, str, str, int, str)

        self.treeview = gtk.TreeView(self.liststore)
        self.treeview.set_rules_hint(True)
        self.treeview.set_search_column(2)
        self.treeview.set_tooltip_column(2)
        self.treeview.columns_autosize()

        self.__create_columns()

        # Events
        self.search_entry.connect('key-release-event', self.__handle_key)
        self.search_button.connect('clicked', self.__on_search)
        self.menu.details.connect('activate', self.__show_details)
        self.treeview.connect('button-press-event', self.__show_menu)
        self.al.signal.connect('al-pref-reset', self.__set_api)
        self.al.signal.connect('al-user-set', self.__enable_control)
        self.al.signal.connect('al-no-user-set', self.__disable_control)
        self.al.signal.connect('al-init-done', self.__init_done)

        # Create scrollbox
        frame = gtk.ScrolledWindow()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        frame.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Pack it together
        frame.add(self.treeview)
        self.pack_start(searchbar, False, False)
        self.pack_start(frame)

        self.__set_api()
        self.menu.show_all()

    # Misc functions ----------------------------------------------------------

    def __set_api(self, widget=None):
        "Set setting for the MAL api."

        self.mal = myanimelist.Anime((
            self.al.config.settings['username'],
            self.al.config.settings['password'],
            self.al.config.api['host'],
            self.al.config.api['user_agent']
            ))

    def __enable_control(self, widget=None):
        "Enable search section when a user has been set."

        self.set_sensitive(True)

    def __disable_control(self, widget=None):
        "Disable search section when no user has been set."

        self.set_sensitive(False)

    def __init_done(self, widget=None):

        self.hide()

    # Widget callbacks --------------------------------------------------------

    def __handle_key(self, widget, event):
        "Handle key events of widgets."

        string, state = event.string, event.state
        keyname =  gtk.gdk.keyval_name(event.keyval)

        if keyname == 'Return':
            self.__on_search(None)

    def __show_menu(self, treeview, event):
        """Displays the main popup menu on a button-press-event
           with options for the selected row in the list."""

        if event.button != 3:  # Only on right click
            return False

        try:
            selection = self.treeview.get_selection()
            row = selection.get_selected_rows()[1][0][0]
            anime_id = int(self.liststore[row][0])
        except IndexError:
            return

        # Disable "Add to" on anime that are already in the list. Or should it be hidden?
        if int(anime_id) in self.already_in_list:
            self.menu.add.set_sensitive(False)
        else:
            self.menu.add.set_sensitive(True)

        self.menu.popup(None, None, None, 3, event.time)

    def __menu_add_anime(self, menuitem, dest_list):
        "Add anime to list."

        selection = self.treeview.get_selection()
        anime_id = int(self.liststore[selection.get_selected_rows()[1][0][0]][0])

        params = {
            'id':                 self.data[anime_id]['id'],
            'title':              self.data[anime_id]['title'],
            'type':               self.data[anime_id]['type'],      # TV, Movie, OVA, ONA, Special, Music
            'episodes':           self.data[anime_id]['episodes'],
            'status':             self.data[anime_id]['status'],    # finished airing, currently airing, not yet aired
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
            table.set_border_width(5)
            table.set_row_spacings(10)
            table.set_col_spacings(10)

            table.attach(gtk.Label('Episodes'), 0, 1, 0, 1)
            table.attach(gtk.Label('Score'), 0, 1, 1, 2)
            table.attach(episodes_entry, 1, 2, 0, 1)
            table.attach(score_entry, 1, 2, 1, 2)

            table.show_all()

            # Dialog flags and buttons
            flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
            buttons = (
                gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
                )

            if dest_list == 1: # If added to "completed"
                episodes_entry.set_text(str(params['episodes']))
                episodes_entry.set_sensitive(False)
                score_entry.grab_focus()

            # Create dialog
            dialog = gtk.Dialog('Add anime', self.al.window, flags, buttons)
            dialog.set_default_response(gtk.RESPONSE_ACCEPT)
            dialog.vbox.pack_start(table, False, True, 5)

            if dialog.run() == gtk.RESPONSE_ACCEPT:

                my_episodes = episodes_entry.get_text()
                my_score = score_entry.get_text()

                try:
                    params['watched_episodes'] = int(my_episodes)
                except ValueError:
                    pass

                try:
                    my_score = int(my_score)

                    if my_score >= 0 or my_score <= 10:
                        params['score'] = my_score
                except ValueError:
                    pass

                dialog.destroy()
            else:
                dialog.destroy()
                return

        self.al.anime.add(params)

    def __on_search(self, button):
        "Get text from text field and search."

        query = self.search_entry.get_text().strip()

        if len(query) < 3:
            self.al.statusbar.update('Please enter a longer search query.')
            self.search_entry.grab_focus()
            return

        self.__process_search(query)

    def __show_details(self, widget):
        "Show details box when a row is activated."

        def get_data(id):
            return self.mal.details(id)
            #return True

        def set_data(data):

            details.widgets['window'].show_all()
            details.widgets['window'].set_title(data['title'])
            details.widgets['window'].set_icon(utils.get_image('./pixmaps/animelist_logo_32.png'))
            details.widgets['title'].set_markup('<span size="x-large" font_weight="bold">%s</span>' % data['title'])
            data['synopsis'] = utils.strip_html_tags(data['synopsis'].replace('<br>', '\n'))
            details.widgets['synopsis'].set_label(data['synopsis'])
            details.mal_url = 'http://myanimelist.net/anime/%d' % data['id']

            # Related
            markup = []

            for s in data['prequels']:
                markup.append('<b>Prequel:</b> %s' % s['title'])

            for s in data['sequels']:
                markup.append('<b>Sequel:</b> %s' % s['title'])

            for s in data['side_stories']:
                markup.append('<b>Side story:</b> %s' % s['title'])

            for s in data['manga_adaptations']:
                markup.append('<b>Manga:</b> %s' % s['title'])

            if len(markup) > 0:
                details.widgets['related'].set_markup('<span size="small">%s</span>' % '\n'.join(markup))
            else:
                details.widgets['box_related'].hide()

            # Other titles
            markup = []

            for k, v in data['other_titles'].iteritems():
                for s in v:
                    markup.append('<b>%s:</b> %s' % (k.capitalize(), s))

            if len(markup) > 0:
                details.widgets['other_titles'].set_markup('<span size="small">%s</span>' % '\n'.join(markup))
            else:
                details.widgets['box_other_titles'].hide()

            # Information
            markup = (
                '<b>Type:</b> %s' % data['type'],
                '<b>Episodes:</b> %s' % data['episodes'],
                '<b>Status:</b> %s' % data['status'].capitalize(),
                '<b>Genres:</b> %s' % ', '.join(data['genres']),
                '<b>Classification:</b> %s' % data['classification'].replace('&', '&amp;')
                )
            details.widgets['information'].set_markup('<span size="small">%s</span>' % '\n'.join(markup))

            # Statistics
            markup = (
                '<b>Score:</b> %s' % data['members_score'],
                '<b>Ranked:</b> #%s' % data['rank'],
                '<b>Popularity:</b> #%s' % data['popularity_rank'],
                '<b>Members:</b> %s' % data['members_count'],
                '<b>Favorites:</b> %s' % data['favorited_count']
                )
            details.widgets['statistics'].set_markup('<span size="small">%s</span>' % '\n'.join(markup))

            self.al.statusbar.clear()

        def set_image(image):

            if image == False:
                return

            details.widgets['image'].clear()
            details.widgets['image'].set_from_file(image)

        self.al.statusbar.update('Fetching information from MyAnimeList...')

        # GUI
        details = DetailsDialog() # Create details dialog

        # Get anime ID
        selection = self.treeview.get_selection()
        row = selection.get_selected_rows()[1][0][0]
        anime_id = int(self.liststore[row][0])
        image_url = self.data[anime_id]['image']

        t1 = gthreads.AsyncTask(get_data, set_data)
        t1.start(anime_id)

        t2 = gthreads.AsyncTask(self.mal.image, set_image)
        t2.start(image_url)

    # Functions for filling the list with search results ----------------------

    def __process_search(self, query):
        "Send search request and put the results in the list."

        def get_data(query):
            self.data = self.mal.search(query)

        def add_rows():
            if self.data == False:
                self.al.statusbar.update('Search failed. Please try again later.')
                self.search_entry.set_sensitive(True)
                self.search_button.set_sensitive(True)
                self.search_entry.grab_focus()
                return

            for k, v in self.data.iteritems():
                self.liststore.append((
                    v['id'],           # Anime ID (hidden)
                    None,              # Status
                    v['title'],        # Title
                    v['type'],         # Type
                    v['episodes'],     # Episodes
                    v['members_score'] # Score
                    ))

            num_results = len(self.data)
            if num_results > 0:
                self.al.statusbar.update('Found %d anime.' % num_results)
            else:
                self.al.statusbar.update('No anime with that name.')

            self.search_entry.set_sensitive(True)
            self.search_button.set_sensitive(True)
            self.search_entry.grab_focus()

        self.search_entry.set_sensitive(False)
        self.search_button.set_sensitive(False)
        self.al.statusbar.update('Searching...')

        self.liststore.clear()
        self.data = {}
        self.already_in_list = []

        t = gthreads.AsyncTask(get_data, add_rows)
        t.start(query)

    # List display functions --------------------------------------------------

    def __cell_status_display(self, column, cell, model, iter):
        "Set background for status column."

        anime_id = int(model.get_value(iter, 0))
        status = self.data[anime_id]['status']

        cell.set_property('background-gdk', self.al.config.cstatus[status])

    def __cell_title_display(self, column, cell, model, iter):
        "Makes the text bold in rows (animes) that are already in your list."

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

    def __create_columns(self):
        "Create columns."

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