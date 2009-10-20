#!/usr/bin/python

# =============================================================================
# plugins/anime.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os

import gtk
import gobject

from plugin import BasePlugin
from lib import myanimelist, utils
from lib.pygtkhelpers import gthreads

class Plugin(BasePlugin):

    plugin_data = {
        'name': 'anime',
        'fancyname': 'Anime',
        'version': '0.1',
        'description': 'Adds a anime list section.'
        }

    def __init__(self, al):

        self.al = al
        self._load_plugin()

    # Plugin functions

    def _load_plugin(self):

        # Toolbar button
        self.al.gui['toolbar'].insert(self.plugin_data['fancyname'], 0)

        # Main widget
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)

        self.current_tab_id = 0
        self.data, self.liststore, self.treeview, frame = {}, {}, {}, {}

        # Menu
        self.menu = gtk.Menu()
        self.menu.move_to = {}

        self.menu.info = gtk.ImageMenuItem(gtk.STOCK_DIALOG_INFO)
        self.menu.delete = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        self.menu.delete.get_children()[0].set_label('Delete')
        self.menu.move = gtk.ImageMenuItem(gtk.STOCK_GO_FORWARD)
        self.menu.move.get_children()[0].set_label('Move')
        self.menu.refresh = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        self.menu.save = gtk.ImageMenuItem(gtk.STOCK_SAVE)
        self.menu.move_submenu = gtk.Menu()
        self.menu.move.set_submenu(self.menu.move_submenu)

        self.menu.append(self.menu.info)
        self.menu.append(self.menu.delete)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.menu.move)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.menu.refresh)
        self.menu.append(self.menu.save)

        # Create tabs, lists and related stuff
        for k, v in enumerate(self.al.config.anime['status']):

            # Create lists
            self.liststore[k] = gtk.ListStore(int, str, str, str, str, int)
            self.liststore[k].set_sort_func(4, self.__sort_progess)
            #ls_sort = gtk.TreeModelSort(self.liststore[k])
            #ls_sort.set_sort_column_id(2, gtk.SORT_ASCENDING)

            self.treeview[k] = gtk.TreeView(self.liststore[k])
            self.treeview[k].set_rules_hint(True)
            self.treeview[k].set_search_column(2)
            self.treeview[k].set_tooltip_column(2)
            self.treeview[k].columns_autosize()

            self.__create_columns(self.treeview[k], k)

            # Menu
            self.treeview[k].connect('button-press-event', self.__show_menu)
            self.menu.move_to[k] = gtk.MenuItem(v.capitalize())
            self.menu.move_to[k].connect('activate', self.__menu_move_row, k)
            self.menu.move_submenu.append(self.menu.move_to[k])

            # Create scrollbox
            frame[k] = gtk.ScrolledWindow()
            frame[k].set_shadow_type(gtk.SHADOW_ETCHED_IN)
            frame[k].set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

            # Paste it together
            frame[k].add(self.treeview[k])
            self.notebook.append_page(frame[k], gtk.Label(v.capitalize()))

        # Pack
        self.al.gui['box'].pack_start(self.notebook)

        # Events
        self.notebook.connect('switch-page', self.__set_current_tab_id)
        #self.menu.info.connect('activate', self.__show_information)
        self.menu.delete.connect('activate', self.__menu_delete)
        self.menu.refresh.connect('activate', self.refresh)
        self.menu.save.connect('activate', self.save)
        self.al.signal.connect('al-switch-section', self.__switch_section)
        self.al.signal.connect('al-user-verified', self.__w_refresh)

        self.menu.show_all()
        self.al.mal.init_anime()

        #if self.al.config.no_user_defined == False:
        self.fill_lists(self.al.config.settings['startup_refresh'])

    def _unload_plugin(self):
        pass

    def __switch_section(self, widget, section_name):

        if section_name == self.plugin_data['fancyname']:
            self.notebook.show()
        else:
            self.notebook.hide()

    # Misc functions

    def __w_refresh(self, widget=None):
        "A wrapper for 'refresh' function."

        self.al.mal.init_anime()

        # If self.refresh is executed without 'gobject.idle_add' the application
        # will get a 'Segmentation fault'. I'm not sure why this happens.
        gobject.idle_add(self.refresh)

    def __callback(self, result):
        if result == False:
            self.al.gui['statusbar'].update('Could not send changes to MyAnimeList')
            self.al.gui['statusbar'].clear(5000)
        else:
            self.al.gui['statusbar'].clear(1000)

    def save(self, widget=None):
        """Save anime data to local cache. This function is executed when
           the 'save' button is pressed and when the application shuts down."""

        #if self.al.config.no_user_defined == False:
        utils.cache_data('%s/%s_animelist.cpickle' % (self.al.HOME, self.al.config.settings['username']), self.data)

        self.al.gui['statusbar'].update('Saving data to local cache...')
        self.al.gui['statusbar'].clear(1000)

    # Widget callbacks

    def __set_current_tab_id(self, notebook, page, page_num):
        """Update the current tab number and hide the corrent menu item in the
           'Move to' menu. Note: this method is also called when the tabs are
           created (at startup) (each time a tab is created)."""

        self.menu.move_to[self.current_tab_id].show()
        self.current_tab_id = page_num
        self.menu.move_to[self.current_tab_id].hide()

    def __show_menu(self, treeview, event):
        """Displays the main popup menu on a button-press-event
           with options for the selected row in the list."""

        if event.button != 3: # Only on right click
            return False

        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))

        if pthinfo is not None:
            path, col, cellx, celly = pthinfo

            treeview.grab_focus()
            treeview.set_cursor(path, col, 0)

            self.menu.info.set_sensitive(True)
            self.menu.delete.set_sensitive(True)
            self.menu.move.set_sensitive(True)
        else:
            self.menu.info.set_sensitive(False)
            self.menu.delete.set_sensitive(False)
            self.menu.move.set_sensitive(False)

        self.menu.popup(None, None, None, 3, event.time)

    def __menu_delete(self, menuitem):
        "Wrapper for detele()."

        self.delete()

    def __menu_move_row(self, menuitem, dest_list):
        "Wrapper method for move()."

        selection = self.treeview[self.current_tab_id].get_selection()
        unused, rows = selection.get_selected_rows()

        self.move(rows[0][0], self.current_tab_id, dest_list)

    # List display/edit functions

    def fill_lists(self, refresh):
        "Starts __get_data in a thread and __add_rows when the thread is finished to fill the lists with data."

        # Get data from cache or download it from MAL and save it to the local cache.
        def get_data(refresh):

            filename = '%s/%s_animelist.cpickle' % (self.al.HOME, self.al.config.settings['username'])

            if refresh == False:
                if os.path.exists(filename):
                    self.data = utils.get_cache(filename)
                    if self.data is None:
                        refresh = True
                else:
                    refresh = True

            if refresh == True:
                self.data = self.al.mal.anime.list()
                utils.cache_data(filename, self.data)

        # Add all anime data to the lists.
        def add_rows():

            for k, v in enumerate(self.al.config.anime['status']):
                self.liststore[k].clear()

            if self.data is None or self.data == False:
                self.al.gui['statusbar'].update('Could not refresh/update the data.')
                return

            if type(self.data) == type({}): # Temperary
                for k, v in self.data.iteritems():
                    self.liststore[self.al.config.anime['rstatus'][v['watched_status']]].append((
                        v['id'],    # Anime ID (hidden)
                        None,       # Status
                        v['title'], # Title
                        v['type'],  # Type
                        None,       # Progress (watched episodes/episodes)
                        v['score']  # Score
                        ))

            self.al.gui['statusbar'].clear(1000)

        self.al.gui['statusbar'].update('Loading data...')

        t = gthreads.AsyncTask(get_data, add_rows)
        t.start(refresh)

    def refresh(self, widget=None):
        "Wrapper for fill_lists."

        self.fill_lists(True)

    def __cell_status_display(self, column, cell, model, iter):
        "Set background for status column."

        anime_id = model.get_value(iter, 0)
        status = self.data[anime_id]['status']

        cell.set_property('background-gdk', self.al.config.anime['cstatus'][status])

    def __cell_progress_display(self, column, cell, model, iter):
        "Put 'watched episodes/episodes' in column."

        anime_id = model.get_value(iter, 0)
        episodes = self.data[anime_id]['episodes']
        if episodes == 0: episodes = '?'

        cell.set_property('text', '%s/%s' % (self.data[anime_id]['watched_episodes'], episodes))

    def __cell_progress_start_edit(self, cellrenderer, editable, row, list_id):
        "Split the episodes from the watched episodes."

        editable.set_text(editable.get_text().split('/', 1)[0])

    def __create_columns(self, treeview, list_id):
        "Create columns."

        # Anime ID
        column = gtk.TreeViewColumn(None, None)
        column.set_visible(False)
        treeview.append_column(column)

        # Status (color)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(None, renderer, text=1)
        column.set_resizable(False)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(8)
        column.set_cell_data_func(renderer, self.__cell_status_display)
        treeview.append_column(column)

        # Title
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Title', renderer, text=2)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_expand(True)
        treeview.append_column(column)

        # Type (TV, OVA ...)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Type', renderer, text=3)
        column.set_sort_column_id(3)
        treeview.append_column(column)

        # Progess
        renderer = gtk.CellRendererText()
        renderer.set_property('editable', True)
        renderer.connect('editing-started', self.__cell_progress_start_edit, list_id)
        renderer.connect('edited', self.__cell_progress_edited, list_id)
        column = gtk.TreeViewColumn('Progress', renderer, text=4)
        column.set_sort_column_id(4)
        column.set_cell_data_func(renderer, self.__cell_progress_display)
        treeview.append_column(column)

        # Score
        renderer = gtk.CellRendererSpin()
        renderer.set_property('editable', True)
        adjustment = gtk.Adjustment(0, 0, 10, 1)
        renderer.set_property('adjustment', adjustment)
        renderer.connect('edited', self.__cell_score_edited, list_id)
        column = gtk.TreeViewColumn('Score', renderer, text=5)
        column.set_sort_column_id(5)
        treeview.append_column(column)

    def __sort_progess(self, model, iter1, iter2, data=None):
        "Sort the list by progress (total episodes)."

        (c, order) = model.get_sort_column_id()

        if c < 0:
            return 0

        id1 = model.get_value(iter1, 0)
        id2 = model.get_value(iter2, 0)

        x = self.data[int(id1)]['episodes']
        y = self.data[int(id2)]['episodes']

        if x < y:
            return -1
        if x == y:
            return 0

        return 1

    def __cell_progress_edited(self, cellrenderer, row, new_progress, list_id):
        "Validate given progress and update score cell, local cache and MAL."

        anime_id = int(self.liststore[list_id][row][0])
        old_progress = self.data[anime_id]['watched_episodes']
        new_progress = int(new_progress)

        if new_progress != old_progress:

            self.al.gui['statusbar'].update('Sending changes to MyAnimeList...')

            episodes = self.data[anime_id]['episodes']
            if episodes == 0: episodes = '?'

            # This isn't needed because __cell_progress_display already does this
            # self.liststore[list_id][row][4] = '%s/%s' % (new_progress, episodes)
            self.data[anime_id]['watched_episodes'] = new_progress

            # Update MAL
            t = gthreads.AsyncTask(self.al.mal.anime.update, self.__callback)
            t.start(
                anime_id,
                {'status': self.data[anime_id]['watched_status'],
                'episodes': self.data[anime_id]['watched_episodes'],
                'score': self.data[anime_id]['score']})

    def __cell_score_edited(self, cellrenderer, row, new_score, list_id):
        "Validate given score and update score cell, local cache and MAL."

        anime_id = self.liststore[list_id][row][0]
        old_score = self.liststore[list_id][row][5]
        new_score = int(new_score)

        if new_score != old_score and new_score >= 0 and new_score <= 10:

            self.al.gui['statusbar'].update('Sending changes to MyAnimeList...')

            self.liststore[list_id][row][5] = new_score
            self.data[anime_id]['score'] = new_score

            # Update MAL
            t = gthreads.AsyncTask(self.al.mal.anime.update, self.__callback)
            t.start(
                anime_id,
                {'status': self.data[anime_id]['watched_status'],
                'episodes': self.data[anime_id]['watched_episodes'],
                'score': self.data[anime_id]['score']})

    # Functions for adding, removing and updating anime -----------------------

    # Note:
    #  - All these functions are meant for internal use (usage in this class).
    #    Except for 'add', which is used to add anime from the search section.

    def add(self, params):
        "Prepend a row to a list."

        self.al.gui['statusbar'].update('Sending changes to MyAnimeList...')

        self.data[int(params['id'])] = {
            'id':               params['id'],
            'title':            params['title'],
            'type':             params['type'],
            'episodes':         params['episodes'],
            'status':           params['status'],
            'watched_status':   params['watched_status'],
            'watched_episodes': params['watched_episodes'],
            'score':            params['score']
            }

        list_data = (params['id'], None, params['title'], params['type'], None, params['score'])
        self.liststore[self.al.config.anime['rstatus'][params['watched_status']]].insert(0, list_data)

        add_params = {
            'anime_id': params['id'],
            'status':   params['watched_status'],
            'score':    params['score']
            }

        if params['status'] != 'completed':
            add_params['episodes'] = params['watched_episodes']

        t = gthreads.AsyncTask(self.al.mal.anime.add, self.__callback)
        t.start(add_params)

    def delete(self):
        "Removes the selected row from the list."

        self.al.gui['statusbar'].update('Sending changes to MyAnimeList...')

        # Get anime ID and list iter
        selection = self.treeview[self.current_tab_id].get_selection()
        row = selection.get_selected_rows()[1][0][0]
        iter = selection.get_selected()[1]
        anime_id = self.liststore[self.current_tab_id][row][0]

        # Remove anime from list and cache
        self.liststore[self.current_tab_id].remove(iter)
        del self.data[anime_id]

        # Start thread
        t = gthreads.AsyncTask(self.al.mal.anime.delete, self.__callback)
        t.start(anime_id)

    def move(self, row, current_list, dest_list):
        "Move a row to an other list."

        self.al.gui['statusbar'].update('Sending changes to MyAnimeList...')

        anime_id = self.liststore[current_list][row][0]

        # Update local cache
        self.data[anime_id]['watched_status'] = self.al.config.anime['status'][dest_list]
        self.liststore[dest_list].insert(0, self.liststore[current_list][row])

        iter = self.liststore[current_list].get_iter(row)
        self.liststore[current_list].remove(iter)

        # Start thread
        t = gthreads.AsyncTask(self.al.mal.anime.update, self.__callback)
        t.start(
            anime_id,
            {'status': self.data[anime_id]['watched_status'],
            'episodes': self.data[anime_id]['watched_episodes'],
            'score': self.data[anime_id]['score']})















