#!/usr/bin/python

# =============================================================================
# list.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import thread
import os

import gtk

from modules import utils

class Lists():
    def __init__(self, al):

        self.al = al

        # Set variables
        self.current_tab_num = 0
        self.anime_data = {}
        self.liststore = {}
        frame = {}
        self.treeview = {}
        self.move_to_item = {}

        # Menu
        self.menu = gtk.Menu()

        details_row = gtk.MenuItem('Details')
        delete_row = gtk.MenuItem('Delete')
        move_row = gtk.MenuItem('Move to')
        move_row_submenu = gtk.Menu()
        move_row.set_submenu(move_row_submenu)

        self.menu.append(details_row)
        self.menu.append(delete_row)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(move_row)

        # Tabs
        self.tabs = gtk.Notebook()
        self.tabs.set_tab_pos(gtk.POS_TOP)
        self.tabs.connect('switch-page', self.update_current_tab)

        # Loop lists, boxes and tabs together
        for i in self.al.config.lists:

            # Create lists
            self.liststore[i] = gtk.ListStore(str, str, str, str, str)

            self.treeview[i] = gtk.TreeView(self.liststore[i])
            self.treeview[i].set_rules_hint(True)
            self.treeview[i].set_search_column(0)
            self.treeview[i].set_tooltip_column(1)
            self.treeview[i].columns_autosize()
            self.treeview[i].set_reorderable(True)

            self.create_columns(self.treeview[i], i)

            # Menu (events and menu items)
            self.treeview[i].connect('button-press-event', self.show_menu, i)

            self.move_to_item[i] = gtk.MenuItem(self.al.config.lists[i])
            self.move_to_item[i].connect('activate', self.menu_move_row, i)
            move_row_submenu.append(self.move_to_item[i])

            # Create scrollbox
            frame[i] = gtk.ScrolledWindow()
            frame[i].set_shadow_type(gtk.SHADOW_ETCHED_IN)
            frame[i].set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

            # Paste it together
            frame[i].add(self.treeview[i])
            self.tabs.append_page(frame[i], gtk.Label(self.al.config.lists[i]))

        thread.start_new_thread(self.create_rows, (self.al.config.prefs['startup_refresh'],))

        self.menu.show_all()

    #
    #  Update the current tab number and hide the corrent menu item in the "Move to" menu
    #  Note: this method is also called when the tabs are created (at startup) (5 or 6 times).
    #
    def update_current_tab(self, notebook, page, page_num):

        previous_tab = self.al.config.tab_numbers[self.current_tab_num]
        self.move_to_item[previous_tab].show()

        self.current_tab_num = page_num

        current_tab = self.al.config.tab_numbers[self.current_tab_num]
        self.move_to_item[current_tab].hide()

    #
    #  Displays the main popup menu on a button-press-event
    #  with options for the selected row in the list.
    #
    def show_menu(self, treeview, event, list_id):

        if event.button != 3:  # Only on right click
            return False

        time = event.time
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))

        if pthinfo is not None:
            path, col, cellx, celly = pthinfo

            treeview.grab_focus()
            treeview.set_cursor(path, col, 0)

            self.menu.popup(None, None, None, 3, time)

    #
    #  Wrapper method for move_row()
    #
    def menu_move_row(self, menuitem, dest_list):

        current_list = self.al.config.tab_numbers[self.current_tab_num]
        selection = self.treeview[current_list].get_selection()
        unused, rows = selection.get_selected_rows()

        self.move_row(rows[0][0], current_list, dest_list)

    #
    #  Prepend a row to a list
    #  Local cache should be manually updated
    #
    def add_row(self, list_id, data):
        self.liststore[list_id].insert(0, data)

    #
    #  Remove a row from a list
    #  Local cache should be manually updated
    #
    def remove_row(self, list_id, row):
        iter = self.liststore[list_id].get_iter(row)
        self.liststore[list_id].remove(iter)

    #
    #  Move a row to an other list by using add_row and remove_row
    #
    def move_row(self, row, current_list, dest_list):

        anime_id = int(self.liststore[current_list][row][0])

        # Update local cache
        self.anime_data[anime_id][4] = str(dest_list)
        self.add_row(dest_list, self.liststore[current_list][row])
        self.remove_row(current_list, row)

        # Update MAL
        thread.start_new_thread(self._update_anime, (anime_id,
            (self.anime_data[anime_id][5],
            self.anime_data[anime_id][4],
            self.anime_data[anime_id][3])))


    #
    #  Re-download the xml list and update all the lists in the tabs
    #
    def refresh_lists(self):

        for i in self.al.config.lists:
            self.liststore[i].clear()

        thread.start_new_thread(self.create_rows, (True,))

    #
    #  Convert numbers (1, 2, 3) to human readable text (TV, OVA, Movie)
    #
    def cell_type_display(self, column, cell, model, iter):
        cell.set_property('text', self.al.config.types[int(model.get_value(iter, 2))])

    #
    #  Put "my watched episodes/total episodes" in column
    #
    def cell_progress_display(self, column, cell, model, iter):

        anime_id = int(model.get_value(iter, 0))
        episodes = self.anime_data[anime_id][6]
        if episodes == '0': episodes = '?'

        cell.set_property('text', self.anime_data[anime_id][5] + '/' + episodes)

    #
    #  Validate given progress and update score cell, local cache and MAL
    #
    def cell_progress_start_edit(self, cellrenderer, editable, row, list_id):

        editable.set_text(editable.get_text().split('/', 1)[0])

    #
    #  Validate given progress and update score cell, local cache and MAL
    #
    def cell_progress_edited(self, cellrenderer, row, new_progress, list_id):

        anime_id = int(self.liststore[list_id][row][0])
        old_progress = int(self.anime_data[anime_id][5])
        new_progress = int(new_progress)

        if new_progress != old_progress:
            episodes = self.anime_data[anime_id][6]
            if episodes == '0': episodes = '?'

            self.liststore[list_id][row][3] = str(new_progress) + '/' + episodes
            self.anime_data[anime_id][5] = str(new_progress)

            # Update MAL
            thread.start_new_thread(self._update_anime, (anime_id,
                (self.anime_data[anime_id][5],
                self.anime_data[anime_id][4],
                self.anime_data[anime_id][3])))

    #
    #  Validate given score and update score cell, local cache and MAL
    #
    def cell_score_edited(self, cellrenderer, row, new_score, list_id):

        anime_id = int(self.liststore[list_id][row][0])
        old_score = self.liststore[list_id][row][4]
        new_score = int(new_score)

        if new_score != old_score and new_score >= 1 and new_score <= 10:
            self.liststore[list_id][row][4] = new_score
            self.anime_data[anime_id][3] = str(new_score)

            # Update MAL
            thread.start_new_thread(self._update_anime, (anime_id,
                (self.anime_data[anime_id][5],
                self.anime_data[anime_id][4],
                self.anime_data[anime_id][3])))

    #
    #  Update anime
    #
    def _update_anime(self, id, data):

        self.al.update_statusbar('Sending changes to MyAnimeList...')

        mal_response = self.al.mal.update_anime(id,
            (data[0], data[1], data[2]))

        # When an anime could not be updated, a task is created so it can be
        # updated when the program shuts down.
        if mal_response.strip() != 'Updated':
            self.tasks.append({'update': (id, data)})

            self.al.update_statusbar('Could not send changes to MyAnimeList. Changes will be send when the program exits.')
            self.al.clear_statusbar(5000)

            return False

        self.al.clear_statusbar(1000)

        return True

    #
    #  Create rows
    #
    def create_rows(self, refresh=False):

        list_cache = None
        invalid_cache = False
        cache_filename = self.al.HOME + '/' + self.al.config.user['name'] + \
            '_animelist.cpickle'

        if refresh == False:
            if os.path.exists(cache_filename):
                list_cache = utils.get_cache(cache_filename)
                if list_cache is None: invalid_cache = True
            else:
                refresh = True

        if refresh == True or invalid_cache == True:

            if invalid_cache == True:
                self.al.update_statusbar('Cache is not valid. Syncing with MyAnimeList...')
            else:
                self.al.update_statusbar('Syncing with MyAnimeList...')

            xml_data = self.al.mal.fetch_list()
            if xml_data == False:
                self.al.update_statusbar('Data could not be downloaded from MyAnimelist.')
                return False

            list_cache = self.al.mal.parse_list(xml_data)
            utils.cache_data(cache_filename, list_cache)

        # Fill lists
        if not list_cache is None:
            self.anime_data = list_cache
            for k, v in self.anime_data.iteritems():
                self.liststore[int(v[4])].append((
                    v[0], # Anime ID (hidden)
                    v[1], # Title
                    v[2], # Type
                    None, # Progress (Watched episodes/Episodes)
                    v[3]  # Score
                    ))

        self.al.clear_statusbar(1000)

    #
    #  Create columns
    #
    def create_columns(self, treeview, list_id):

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
        column.set_cell_data_func(renderer, self.cell_type_display)
        treeview.append_column(column)

        # Progess
        renderer = gtk.CellRendererText()
        renderer.set_property('editable', True)
        renderer.connect('editing-started', self.cell_progress_start_edit, list_id)
        renderer.connect('edited', self.cell_progress_edited, list_id)
        column = gtk.TreeViewColumn('Progress', renderer, text=3)
        column.set_sort_column_id(3)
        column.set_cell_data_func(renderer, self.cell_progress_display)
        treeview.append_column(column)

        # Score
        renderer = gtk.CellRendererSpin()
        renderer.set_property('editable', True)
        adjustment = gtk.Adjustment(0, 0, 10, 1)
        renderer.set_property('adjustment', adjustment)
        renderer.connect('edited', self.cell_score_edited, list_id)
        column = gtk.TreeViewColumn('Score', renderer, text=4)
        column.set_sort_column_id(4)
        treeview.append_column(column)
