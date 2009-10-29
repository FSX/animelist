#!/usr/bin/python

# =============================================================================
# plugins/search.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gtk
import pango

from plugin import BasePlugin
from lib import utils
from lib.pygtkhelpers import gthreads

class Plugin(BasePlugin):
    """The search plugin. Search results can be added to the anime list (if the
       anime list plugin is enabled ofcourse."""

    plugin_data = {
        'name': 'search',
        'fancyname': 'Search',
        'version': '0.1',
        'description': 'Adds a anime/manga search section.'
        }

    def __init__(self, al):

        self.al = al
        self.anime_plugin_loaded = False
        self._load_plugin()

    def _load_plugin(self, widget=None):

        # Toolbar button
        self.al.gui['toolbar'].insert(self.plugin_data['fancyname'], 1)

        # GUI
        self.box = gtk.VBox()

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

        self.menu.info = gtk.ImageMenuItem(gtk.STOCK_DIALOG_INFO)
        self.menu.add = gtk.ImageMenuItem(gtk.STOCK_ADD)
        self.menu.add.get_children()[0].set_label('Add to...')
        self.menu.add_submenu = gtk.Menu()
        self.menu.add.set_submenu(self.menu.add_submenu)

        self.menu.append(self.menu.info)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.menu.add)

        for k, v in enumerate(self.al.config.anime['status']):
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

        # Create scrollbox
        frame = gtk.ScrolledWindow()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        frame.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Pack it together
        frame.add(self.treeview)
        self.box.pack_start(searchbar, False, False)
        self.box.pack_start(frame)

        self.menu.show_all()

        if self.al.mal.anime is None:
            self.al.mal.init_anime()

        self.al.gui['box'].pack_start(self.box)

        # Events
        self.al.signal.connect('al-switch-section', self.__switch_section)
        self.search_entry.connect('key-release-event', self.__handle_key)
        self.search_button.connect('clicked', self.__on_search)
        self.menu.info.connect('activate', self.__show_information)
        self.treeview.connect('button-press-event', self.__show_menu)
        self.al.signal.connect('al-plugin-init-done', self.__plugin_init_done)
        self.al.signal.connect('al-user-verified', self.__reset_api)

    def _unload_plugin(self):
        pass

    def __switch_section(self, widget, section_name):

        if section_name == self.plugin_data['fancyname']:
            self.box.show()
        else:
            self.box.hide()

    def __plugin_init_done(self, widget=None):
        "Check if anime plugin has been loaded."

        if 'anime' in self.al.plugins:
            self.anime_plugin_loaded = True

    # Misc functions

    def __reset_api(self, widget=None):
            self.al.mal.init_anime()

    # Widget callbacks

    def __handle_key(self, widget, event):
        "Handle key events of widgets."

        string, state = event.string, event.state
        keyname =  gtk.gdk.keyval_name(event.keyval)

        if keyname == 'Return':
            self.__on_search(None)

    def __show_menu(self, treeview, event):
        """Displays the main popup menu on a button-press-event
           with options for the selected row in the list."""

        if event.button != 3 or self.anime_plugin_loaded == False:  # Only on right click
            return False

        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))

        if pthinfo is not None:
            self.menu.info.set_sensitive(True)

            path, col, cellx, celly = pthinfo
            treeview.grab_focus()
            treeview.set_cursor(path, col, 0)
            anime_id = int(self.liststore[path][0])

            # Disable "Add to" on anime that are already in the list. Or should it be hidden?
            if int(anime_id) in self.already_in_list:
                self.menu.add.set_sensitive(False)
            else:
                self.menu.add.set_sensitive(True)
        else:
            self.menu.info.set_sensitive(False)
            self.menu.add.set_sensitive(False)

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
            'watched_status':     self.al.config.anime['status'][dest_list],
            'watched_episodes':   0,
            'score':              0,
            'image':              self.data[anime_id]['image']
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
            dialog = gtk.Dialog('Add anime', self.al.gui['window'], flags, buttons)
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

        self.al.plugins['anime'].add(params)

    def __on_search(self, button):
        "Get text from text field and search."

        query = self.search_entry.get_text().strip()

        if len(query) < 3:
            self.al.statusbar.update('Please enter a longer search query.')
            self.search_entry.grab_focus()
            return

        self.__process_search(query)

    def __show_information(self, widget):
        "Show anime information window."

        # Get anime ID
        selection = self.treeview.get_selection()
        row = selection.get_selected_rows()[1][0][0]
        anime_id = int(self.liststore[row][0])
        image_url = self.data[anime_id]['image']

        self.al.plugins['anime'].show_information_window(anime_id, image_url)

    # Functions for filling the list with search results

    def __process_search(self, query):
        "Send search request and put the results in the list."

        def get_data(query):
            self.data = self.al.mal.anime.search(query)

        def add_rows():
            if self.data == False:
                self.al.gui['statusbar'].update('Search failed. Please try again later.')
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
                self.al.gui['statusbar'].update('Found %d anime.' % num_results)
            else:
                self.al.gui['statusbar'].update('No anime with that name.')

            self.search_entry.set_sensitive(True)
            self.search_button.set_sensitive(True)
            self.search_entry.grab_focus()

        self.search_entry.set_sensitive(False)
        self.search_button.set_sensitive(False)
        self.al.gui['statusbar'].update('Searching...')

        self.liststore.clear()
        self.data = {}
        self.already_in_list = []

        t = gthreads.AsyncTask(get_data, add_rows)
        t.start(query)

    # List display functions

    def __cell_status_display(self, column, cell, model, iter):
        "Set background for status column."

        anime_id = int(model.get_value(iter, 0))
        status = self.data[anime_id]['status']

        cell.set_property('background-gdk', self.al.config.anime['cstatus'][status])

    def __cell_title_display(self, column, cell, model, iter):
        "Makes the text bold in rows (animes) that are already in your list."

        if self.anime_plugin_loaded == False:
            return

        anime_id = int(model.get_value(iter, 0))

        if anime_id in self.al.plugins['anime'].data:
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
