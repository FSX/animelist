#!/usr/bin/python

# =============================================================================
# sections/anime.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os

import gtk

from lib import myanimelist, utils

class Anime(gtk.Notebook):

    def __init__(self, al):

        self.al = al
        gtk.Notebook.__init__(self)

        self.current_tab_id = 0
        self.liststore, self.treeview, frame = {}, {}, {}
        self.al.shutdown_funcs.append('self.anime.save')

        self.set_tab_pos(gtk.POS_TOP)
        self.connect('switch-page', self.__set_current_tab_id)

        # Menu
        self.menu = gtk.Menu()
        self.menu.move_to = {}

        self.menu.details = gtk.MenuItem('Details')
        self.menu.delete = gtk.MenuItem('Delete')
        self.menu.move = gtk.MenuItem('Move to')
        self.menu.move_submenu = gtk.Menu()
        self.menu.move.set_submenu(self.menu.move_submenu)

        self.menu.append(self.menu.details)
        self.menu.append(self.menu.delete)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.menu.move)

        self.menu.delete.connect('activate', self.__menu_delete)

        # Create tabs, lists and related stuff
        for k, v in enumerate(self.al.config.status):

            # Create lists
            self.liststore[k] = gtk.ListStore(str, str, str, str, str, str)
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
            self.append_page(frame[k], gtk.Label(v.capitalize()))

        # Set setting for the MAL api
        self.mal = myanimelist.Anime((
            self.al.config.settings['username'],
            self.al.config.settings['password'],
            self.al.config.api['host'],
            self.al.config.api['user_agent']
            ))

        if self.al.config.no_user_defined == False:
            utils.sthread(self.__create_rows, (self.al.config.settings['startup_refresh'],))

        self.menu.show_all()

    #
    #  Refresh lists
    #
    def refresh(self):
        utils.sthread(self.__create_rows, (True,))

    #
    #  Save data to local cache
    #
    def save(self):
        utils.cache_data('%s/%s_animelist.cpickle' % (self.al.HOME, self.al.config.settings['username']), self.data)

        self.al.statusbar.update('Saving data to local cache...')
        self.al.statusbar.clear(2000)

    #
    #  Prepend a row to a list
    #
    def add(self, params):
        utils.sthread(self.__add, (params,))

    #
    #  Remove a row from a list (not used)
    #
    def remove(self, id):
        utils.sthread(self.__delete, (id,))

    #
    #  Move a row to an other list by using add_row and remove_row
    #
    def move(self, row, current_list, dest_list):

        anime_id = int(self.liststore[current_list][row][0])

        # Update local cache
        self.data[anime_id]['watched_status'] = self.al.config.status[dest_list]
        self.liststore[dest_list].insert(0, self.liststore[current_list][row])

        iter = self.liststore[current_list].get_iter(row)
        self.liststore[current_list].remove(iter)

        # Update MAL
        utils.sthread(self.__update,
            (anime_id,
            (self.data[anime_id]['watched_status'],
            self.data[anime_id]['watched_episodes'],
            self.data[anime_id]['score'])))

    #
    #  Add anime
    #
    def __add(self, params):

        self.al.statusbar.update('Sending changes to MyAnimeList...')

        response = self.mal.add(params)

        if response == False:
            self.al.statusbar.update('Could not send changes to MyAnimeList.')
            self.al.statusbar.clear(5000)

            return False

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
        self.liststore[self.al.config.rstatus[params['watched_status']]].insert(0, list_data)

        self.al.statusbar.clear(1000)

    #
    #  Update anime. data = (status, episodes, score)
    #
    def __update(self, id, data):

        self.al.statusbar.update('Sending changes to MyAnimeList...')

        response = self.mal.update(id, (data[0], data[1], data[2]))

        if response == False:
            self.al.statusbar.update('Could not send changes to MyAnimeList.')
            self.al.statusbar.clear(5000)

            return False

        self.al.statusbar.clear(1000)

    #
    #  Delete anime. data = (status, episodes, score)
    #
    def __delete(self, id):

        self.al.statusbar.update('Sending changes to MyAnimeList...')

        response = self.mal.delete(id)

        if response == False:
            self.al.statusbar.update('Could not send changes to MyAnimeList.')
            self.al.statusbar.clear(5000)

            return False

        self.al.statusbar.clear(1000)

    #
    #  Update the current tab number and hide the corrent menu item in the
    #  "Move to" menu. Note: this method is also called when the tabs are
    #  created (at startup) (each time a tab is created).
    #
    def __set_current_tab_id(self, notebook, page, page_num):

        self.menu.move_to[self.current_tab_id].show()
        self.current_tab_id = page_num
        self.menu.move_to[self.current_tab_id].hide()

    #
    #  Displays the main popup menu on a button-press-event
    #  with options for the selected row in the list.
    #
    def __show_menu(self, treeview, event):

        if event.button != 3:  # Only on right click
            return False

        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))

        if pthinfo is not None:
            self.selected_path, col, cellx, celly = pthinfo

            treeview.grab_focus()
            treeview.set_cursor(self.selected_path, col, 0)

            self.menu.popup(None, None, None, 3, event.time)

    #
    #  Remove row/anime from list, cache and MAL
    #
    def __menu_delete(self, menuitem):

        selection = self.treeview[self.current_tab_id].get_selection()
        row = selection.get_selected_rows()[1][0][0]
        iter = selection.get_selected()[1]

        anime_id = int(self.liststore[self.current_tab_id][row][0])

        self.liststore[self.current_tab_id].remove(iter)
        del self.data[anime_id]

        # Update MAL
        utils.sthread(self.__delete, (anime_id,))


    #
    #  Wrapper method for move()
    #
    def __menu_move_row(self, menuitem, dest_list):

        selection = self.treeview[self.current_tab_id].get_selection()
        unused, rows = selection.get_selected_rows()

        self.move(rows[0][0], self.current_tab_id, dest_list)

    #
    #  Create rows
    #
    def __create_rows(self, refresh=False):

        invalid_cache = False
        cache_filename = '%s/%s_animelist.cpickle' % (self.al.HOME, self.al.config.settings['username'])

        if refresh == False:
            if os.path.exists(cache_filename):
                list_data = utils.get_cache(cache_filename)
                if list_data is None: invalid_cache = True
            else:
                refresh = True

        if refresh == True or invalid_cache == True:
            if invalid_cache == True:
                self.al.statusbar.update('Cache is not valid. Syncing with MyAnimeList...')
            else:
                self.al.statusbar.update('Syncing with MyAnimeList...')

                for k, v in enumerate(self.al.config.status):
                    self.liststore[k].clear()

            list_data = self.mal.list()
            if list_data == False:
                self.al.statusbar.update('Data could not be downloaded from MyAnimelist.')
                return False

            utils.cache_data(cache_filename, list_data)

        # Fill lists
        self.data = list_data
        for k, v in self.data.iteritems():
            self.liststore[self.al.config.rstatus[v['watched_status']]].append((
                v['id'],    # Anime ID (hidden)
                None,       # Status
                v['title'], # Title
                v['type'],  # Type
                None,       # Progress (watched episodes/episodes)
                v['score']  # Score
                ))

        self.al.statusbar.clear(1000)

    #
    #  Set background for status column
    #
    def __cell_status_display(self, column, cell, model, iter):

        anime_id = int(model.get_value(iter, 0))
        status = self.data[anime_id]['status']

        cell.set_property('background-gdk', self.al.config.cstatus[status])

    #
    #  Put "watched episodes/episodes" in column
    #
    def __cell_progress_display(self, column, cell, model, iter):

        anime_id = int(model.get_value(iter, 0))
        episodes = self.data[anime_id]['episodes']
        if episodes == 0: episodes = '?'

        cell.set_property('text', '%s/%s' % (self.data[anime_id]['watched_episodes'], episodes))

    #
    #  Split the episodes from the watched episodes
    #
    def __cell_progress_start_edit(self, cellrenderer, editable, row, list_id):

        self.selected_path = None # Don't unselect row when editing
        editable.set_text(editable.get_text().split('/', 1)[0])

    #
    #  Validate given progress and update score cell, local cache and MAL
    #
    def __cell_progress_edited(self, cellrenderer, row, new_progress, list_id):

        anime_id = int(self.liststore[list_id][row][0])
        old_progress = int(self.data[anime_id]['watched_episodes'])
        new_progress = int(new_progress)

        if new_progress != old_progress:

            episodes = self.data[anime_id]['episodes']
            if episodes == '0': episodes = '?'

            # This isn't needed because __cell_progress_display already does this
            # self.liststore[list_id][row][4] = '%s/%s' % (new_progress, episodes)
            self.data[anime_id]['watched_episodes'] = unicode(new_progress)

            # Update MAL
            utils.sthread(self.__update,
                (anime_id,
                (self.data[anime_id]['watched_status'],
                self.data[anime_id]['watched_episodes'],
                self.data[anime_id]['score'])))

    #
    #  Don't unselect row when editing
    #
    def __cell_score_start_edit(self, cellrenderer, editable, row):
        self.selected_path = None

    #
    #  Validate given score and update score cell, local cache and MAL
    #
    def __cell_score_edited(self, cellrenderer, row, new_score, list_id):

        anime_id = int(self.liststore[list_id][row][0])
        old_score = self.liststore[list_id][row][5]
        new_score = int(new_score)

        if new_score != old_score and new_score >= 0 and new_score <= 10:
            self.liststore[list_id][row][5] = new_score
            self.data[anime_id]['score'] = unicode(new_score)

            # Update MAL
            utils.sthread(self.__update,
                (anime_id,
                (self.data[anime_id]['watched_status'],
                self.data[anime_id]['watched_episodes'],
                self.data[anime_id]['score'])))

    #
    #  Create columns
    #
    def __create_columns(self, treeview, list_id):

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
        #column.set_cell_data_func(renderer, self._cell_type_display)
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
        renderer.connect('editing-started', self.__cell_score_start_edit)
        renderer.connect('edited', self.__cell_score_edited, list_id)
        column = gtk.TreeViewColumn('Score', renderer, text=5)
        column.set_sort_column_id(5)
        treeview.append_column(column)
