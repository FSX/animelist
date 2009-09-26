#!/usr/bin/python

# =============================================================================
# sections/anime.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os

import gobject
import gtk

from lib import myanimelist, utils
from lib.dialogs import DetailsDialog
from lib.pygtkhelpers import gthreads

class Anime(gtk.Notebook):

    def __init__(self, al):

        self.al = al
        gtk.Notebook.__init__(self)
        self.set_tab_pos(gtk.POS_TOP)
        self.connect('switch-page', self.__set_current_tab_id)

        self.current_tab_id = 0
        self.data, self.liststore, self.treeview, frame = {}, {}, {}, {}

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

        self.__set_api()
        self.menu.show_all()

        # Events
        self.menu.details.connect('activate', self.__show_details)
        self.menu.delete.connect('activate', self.__menu_delete)
        self.al.signal.connect('al-shutdown', self.save)
        self.al.signal.connect('al-pref-reset', self.__set_api)
        self.al.signal.connect('al-pref-reset', self.__w_refresh)
        self.al.signal.connect('al-user-set', self.__enable_control)
        self.al.signal.connect('al-no-user-set', self.__disable_control)

        if self.al.config.no_user_defined == False:
            self.fill_lists(self.al.config.settings['startup_refresh'])

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
        "Enable anime section when a user has been set."

        self.set_sensitive(True)

    def __disable_control(self, widget=None):
        "Disable anime section when no user has been set."

        self.set_sensitive(False)

    def __w_refresh(self, widget=None):
        "A wrapper for 'refresh' function."

        # If self.refresh is executed with out 'gobject.idle_add' the
        # application will get a 'Segmentation fault'.
        gobject.idle_add(self.refresh)

    def save(self, widget=None):
        """Save anime data to local cache. This function is executed when
           the 'save' button is pressed and when the application shuts down."""

        utils.cache_data('%s/%s_animelist.cpickle' % (self.al.HOME, self.al.config.settings['username']), self.data)

        self.al.statusbar.update('Saving data to local cache...')
        self.al.statusbar.clear(2000)

    # Widget callbacks --------------------------------------------------------

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

            self.menu.popup(None, None, None, 3, event.time)

    def __menu_delete(self, menuitem):
        "Wrapper for detele()."

        self.delete()

    def __menu_move_row(self, menuitem, dest_list):
        "Wrapper method for move()."

        selection = self.treeview[self.current_tab_id].get_selection()
        unused, rows = selection.get_selected_rows()

        self.move(rows[0][0], self.current_tab_id, dest_list)

    def __show_details(self, widget):
        "Show details box when a row is activated."

        def get_data(id):
            return self.mal.details(id)
            #return True

        def set_data(data):

            details.widgets['window'].show_all()
            details.widgets['title'].set_markup('<span size="x-large" font_weight="bold">%s</span>' % data['title'])

            data['synopsis'] = utils.strip_html_tags(data['synopsis'].replace('<br>', '\n'))
            details.widgets['synopsis'].set_label(data['synopsis'])

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

        def get_image(url):

            import urllib

            path = self.al.HOME + '/cache/'
            filename = os.path.basename(url)

            if not os.access(path, os.F_OK | os.W_OK):
                os.mkdir(path)

            urllib.urlretrieve(url, path + filename)

            return gtk.gdk.pixbuf_new_from_file(path + filename)

        def set_image(gdk_image):

            details.widgets['image'].clear()
            details.widgets['image'].set_from_pixbuf(gdk_image)

        self.al.statusbar.update('Fetching information from MyAnimeList...')

        # GUI
        details = DetailsDialog() # Create details dialog

        # Get anime ID
        selection = self.treeview[self.current_tab_id].get_selection()
        row = selection.get_selected_rows()[1][0][0]
        anime_id = int(self.liststore[self.current_tab_id][row][0])
        image_url = self.data[anime_id]['image']

        t1 = gthreads.AsyncTask(get_data, set_data)
        t1.start(anime_id)

        t2 = gthreads.AsyncTask(get_image, set_image)
        t2.start(image_url)

    # List display functions --------------------------------------------------

    def __cell_status_display(self, column, cell, model, iter):
        "Set background for status column."

        anime_id = int(model.get_value(iter, 0))
        status = self.data[anime_id]['status']

        cell.set_property('background-gdk', self.al.config.cstatus[status])

    def __cell_progress_display(self, column, cell, model, iter):
        "Put 'watched episodes/episodes' in column."

        anime_id = int(model.get_value(iter, 0))
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

    # Functions for refreshing the anime lists --------------------------------

    def fill_lists(self, refresh):
        "Starts __get_data in a thread and __add_rows when the thread is finished to fill the lists with data."

        def get_data(refresh):
            "Get data from cache or download it from MAL and save it to the local cache."

            filename = '%s/%s_animelist.cpickle' % (self.al.HOME, self.al.config.settings['username'])

            if refresh == False:
                if os.path.exists(filename):
                    self.data = utils.get_cache(filename)
                    if self.data is None:
                        refresh = True
                else:
                    refresh = True

            if refresh == True :
                self.data = self.mal.list()
                utils.cache_data(filename, self.data)

        def add_rows():
            "Add all anime data to the lists."

            for k, v in enumerate(self.al.config.status):
                self.liststore[k].clear()

            if self.data is None:
                self.al.statusbar.update('Could not refresh/update the data.')
                return

            if type(self.data) == type({}): # Temperary
                for k, v in self.data.iteritems():
                    self.liststore[self.al.config.rstatus[v['watched_status']]].append((
                        v['id'],    # Anime ID (hidden)
                        None,       # Status
                        v['title'], # Title
                        v['type'],  # Type
                        None,       # Progress (watched episodes/episodes)
                        v['score']  # Score
                        ))

            self.al.statusbar.clear(2000)

        self.al.statusbar.update('Syncing with MyAnimeList...')

        t = gthreads.AsyncTask(get_data, add_rows)
        t.start(refresh)

    def refresh(self):
        "Wrapper for fill_lists."

        self.fill_lists(True)

    # Functions for adding, removing and updating anime -----------------------

    # Note:
    #  - All these functions are meant for internal use (usage in this class).
    #    Except for 'add', which is used to add anime from the search section.

    def add(self, params):
        "Prepend a row to a list."

        self.al.statusbar.update('Sending changes to MyAnimeList...')

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

        add_params = {
            'anime_id': params['id'],
            'status':   params['watched_status'],
            'score':    params['score']
            }

        if params['status'] != 'completed':
            add_params['episodes'] = params['watched_episodes']

        t = gthreads.AsyncTask(self.mal.add, self.__callback)
        t.start(add_params)

    def delete(self):
        "Removes the selected row from the list."

        self.al.statusbar.update('Sending changes to MyAnimeList...')

        # Get anime ID and list iter
        selection = self.treeview[self.current_tab_id].get_selection()
        row = selection.get_selected_rows()[1][0][0]
        iter = selection.get_selected()[1]
        anime_id = int(self.liststore[self.current_tab_id][row][0])

        # Remove anime from list and cache
        self.liststore[self.current_tab_id].remove(iter)
        del self.data[anime_id]

        # Start thread
        t = gthreads.AsyncTask(self.mal.delete, self.__callback)
        t.start(anime_id)

    def move(self, row, current_list, dest_list):
        "Move a row to an other list."

        self.al.statusbar.update('Sending changes to MyAnimeList...')

        anime_id = int(self.liststore[current_list][row][0])

        # Update local cache
        self.data[anime_id]['watched_status'] = self.al.config.status[dest_list]
        self.liststore[dest_list].insert(0, self.liststore[current_list][row])

        iter = self.liststore[current_list].get_iter(row)
        self.liststore[current_list].remove(iter)

        # Start thread
        t = gthreads.AsyncTask(self.mal.update, self.__callback)
        t.start(
            anime_id,
            {'status': self.data[anime_id]['watched_status'],
            'episodes': self.data[anime_id]['watched_episodes'],
            'score': self.data[anime_id]['score']})

    def __cell_progress_edited(self, cellrenderer, row, new_progress, list_id):
        "Validate given progress and update score cell, local cache and MAL."

        anime_id = int(self.liststore[list_id][row][0])
        old_progress = int(self.data[anime_id]['watched_episodes'])
        new_progress = int(new_progress)

        if new_progress != old_progress:

            self.al.statusbar.update('Sending changes to MyAnimeList...')

            episodes = self.data[anime_id]['episodes']
            if episodes == '0': episodes = '?'

            # This isn't needed because __cell_progress_display already does this
            # self.liststore[list_id][row][4] = '%s/%s' % (new_progress, episodes)
            self.data[anime_id]['watched_episodes'] = unicode(new_progress)

            # Update MAL
            t = gthreads.AsyncTask(self.mal.update, self.__callback)
            t.start(
                anime_id,
                {'status': self.data[anime_id]['watched_status'],
                'episodes': self.data[anime_id]['watched_episodes'],
                'score': self.data[anime_id]['score']})

    def __cell_score_edited(self, cellrenderer, row, new_score, list_id):
        "Validate given score and update score cell, local cache and MAL."

        anime_id = int(self.liststore[list_id][row][0])
        old_score = int(self.liststore[list_id][row][5])
        new_score = int(new_score)

        if new_score != old_score and new_score >= 0 and new_score <= 10:

            self.al.statusbar.update('Sending changes to MyAnimeList...')

            self.liststore[list_id][row][5] = new_score
            self.data[anime_id]['score'] = unicode(new_score)

            # Update MAL
            t = gthreads.AsyncTask(self.mal.update, self.__callback)
            t.start(
                anime_id,
                {'status': self.data[anime_id]['watched_status'],
                'episodes': self.data[anime_id]['watched_episodes'],
                'score': self.data[anime_id]['score']})

    def __callback(self, result):
        if result == False:
            self.al.statusbar.update('Could not send changes to MyAnimeList.')
            self.al.statusbar.clear(5000)
        else:
            self.al.statusbar.clear(1000)
