#!/usr/bin/python

# =============================================================================
# plugins/anime.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import os
import webbrowser

import gtk
import gobject

from lib.plugin import BasePlugin
from lib import utils
from lib.pygtkhelpers import gthreads

class Plugin(BasePlugin):
    """The anime list plugin.  A list with all the animes from the user's MAL list
    divided into different statuses (completed, watching, etc.).  Functions for
    editing the list are also available for other plugins.
    """

    plugin_data = {
        'name': 'anime',
        'fancyname': 'Anime',
        'version': '0.1',
        'description': 'Adds a anime list section.'
        }

    def __init__(self, al):
        BasePlugin.__init__(self, al)

    def _load_plugin(self, widget=None):

        # Toolbar button
        self.al.gui['toolbar'].insert(self.plugin_data['fancyname'], 0)

        # Main widget
        self.main_gui = gtk.Notebook()
        self.main_gui.set_tab_pos(gtk.POS_TOP)

        self.current_tab_id = 0
        self.data, self.liststore, self.treeview, self.tab_label, self.frame = {}, {}, {}, {}, {}

        # Menu
        self.menu = gtk.Menu()
        self.menu.move_to = {}

        self.menu.info = gtk.ImageMenuItem(gtk.STOCK_DIALOG_INFO)
        self.menu.delete = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        self.menu.delete.get_children()[0].set_label('Delete')
        self.menu.move = gtk.ImageMenuItem(gtk.STOCK_GO_FORWARD)
        self.menu.move.get_children()[0].set_label('Move')
        self.menu.copy_title = gtk.ImageMenuItem(gtk.STOCK_COPY)
        self.menu.copy_title.get_children()[0].set_label('Copy title')
        self.menu.refresh = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        self.menu.save = gtk.ImageMenuItem(gtk.STOCK_SAVE)
        self.menu.move_submenu = gtk.Menu()
        self.menu.move.set_submenu(self.menu.move_submenu)

        self.menu.append(self.menu.info)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.menu.delete)
        self.menu.append(self.menu.move)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.menu.copy_title)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.menu.refresh)
        self.menu.append(self.menu.save)

        # Create tabs, lists and related stuff
        for k, v in enumerate(self.al.config.anime['status']):

            # Create lists
            self.liststore[k] = gtk.ListStore(int, str, str, str, str, int)
            self.liststore[k].set_sort_func(4, self._sort_progess)

            # Enabling this causes problems with moving/updating anime
            #ls_sort = gtk.TreeModelSort(self.liststore[k])
            #ls_sort.set_sort_column_id(2, gtk.SORT_ASCENDING)

            self.treeview[k] = gtk.TreeView(self.liststore[k])
            self.treeview[k].set_rules_hint(True)
            self.treeview[k].set_search_column(2)
            self.treeview[k].set_tooltip_column(2)
            self.treeview[k].columns_autosize()

            self._create_columns(self.treeview[k], k)

            # Menu
            self.treeview[k].connect('button-press-event', self._show_menu)
            self.menu.move_to[k] = gtk.MenuItem(v.capitalize())
            self.menu.move_to[k].connect('activate', self._menu_move_row, k)
            self.menu.move_submenu.append(self.menu.move_to[k])

            # Create scrollbox
            self.frame[k] = gtk.ScrolledWindow()
            self.frame[k].set_shadow_type(gtk.SHADOW_ETCHED_IN)
            self.frame[k].set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

            # Paste it together
            self.frame[k].add(self.treeview[k])
            self.main_gui.append_page(self.frame[k], gtk.Label(v.capitalize()))

        # Pack
        self.al.gui['box'].pack_start(self.main_gui)

        # Events
        self.main_gui.connect('switch-page', self._set_current_tab_id)
        self.menu.info.connect('activate', self._show_information)
        self.menu.delete.connect('activate', self._menu_delete)
        self.menu.copy_title.connect('activate', self._copy_anime_title)
        self.menu.refresh.connect('activate', self.refresh)
        self.menu.save.connect('activate', self.save)
        self.al.signal.connect('al-switch-section', self._switch_section)
        self.al.signal.connect('al-shutdown-lvl2', self.save)
        self.al.signal.connect('al-user-verified', self._w_refresh)

        # Make menu visible
        self.menu.show_all()

        # Activate anime API if it isn't
        if self.al.mal.anime is None:
            self.al.mal.init_anime()

        # Only load the anime list if the configured user has been verified
        if self.al.config.user_verified == True:
            self.fill_lists(self.al.config.settings['startup_refresh'])

    def _unload_plugin(self):
        pass

    def _switch_section(self, widget, section_name):

        if section_name == self.plugin_data['fancyname']:
            self.main_gui.show()
        else:
            self.main_gui.hide()

    # Misc functions

    def _w_refresh(self, widget=None):
        # Private.  A wrapper for 'refresh' function.

        self.al.mal.init_anime()

        # If self.refresh is executed without 'gobject.idle_add' the application
        # will get a 'Segmentation fault'.  I'm not sure why this happens.
        gobject.idle_add(self.refresh)

    def _clear_message(self, result):
        # Private.  This function is called by some funtions when a request has been finished.

        if result == False:
            self.al.gui['statusbar'].update('Anime: Could not send changes to MyAnimeList')
            self.al.gui['statusbar'].clear(5000)
        else:
            self.al.gui['statusbar'].clear(1000)

    def save(self, widget=None):
        """Save anime data to local cache. This function is executed when
        the 'save' button is pressed and when the application shuts down.
        """

        #if self.al.config.no_user_defined == False:
        utils.cache_data('%s/%s_animelist.cpickle' % (self.al.HOME, self.al.config.settings['username']), self.data)

        self.al.gui['statusbar'].update('Anime: Saving data to local cache...')
        self.al.gui['statusbar'].clear(1000)

    def show_information_window(self, anime_id, image_url):
        """Fetch all the information (and image) and how the information window.
        This is just a wrapper for the InfoWindow class.
        """

        def request_data(aid):
            return self.al.mal.anime.details(aid)

        def cb_set_info(data):

            window.set_info(data)
            self.al.gui['statusbar'].clear()

        def cb_set_image(image):

            if not image:
                return

            window.set_image(image)

        self.al.gui['statusbar'].update('Anime: Fetching information from MyAnimeList...')
        window = InfoWindow('%s/plugins/anime/anime.ui' % self.al.path)

        t1 = gthreads.AsyncTask(request_data, cb_set_info)
        t1.start(anime_id)

        t2 = gthreads.AsyncTask(self.al.mal.anime.image, cb_set_image)
        t2.start(image_url)

    def _update_item_count(self):
        # Private.  Display the amount of item/rows of the lists in the tabs.

        for k, v in enumerate(self.al.config.anime['status']):
            self.main_gui.set_tab_label(self.frame[k], gtk.Label('%s (%d)' % (v.capitalize(), len(self.liststore[k]))))

    # Widget callbacks

    def _set_current_tab_id(self, notebook, page, page_num):
        # Private.  Update the current tab number and hide the corrent menu item in the
        # 'Move to' menu.  Note: this method is also called when the tabs are
        # created (at startup) (each time a tab is created)."""

        self.menu.move_to[self.current_tab_id].show()
        self.current_tab_id = page_num
        self.menu.move_to[self.current_tab_id].hide()

    def _show_menu(self, treeview, event):
        # Private.  Displays the main popup menu on a button-press-event
        # with options for the selected row in the list.

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
            self.menu.copy_title.set_sensitive(True)
        else:
            self.menu.info.set_sensitive(False)
            self.menu.delete.set_sensitive(False)
            self.menu.move.set_sensitive(False)
            self.menu.copy_title.set_sensitive(False)

        self.menu.popup(None, None, None, 3, event.time)

    def _menu_delete(self, widget):
        # Private.  Wrapper for detele().

        self.delete()

    def _menu_move_row(self, widget, dest_list):
        # Private.  Wrapper method for move().

        selection = self.treeview[self.current_tab_id].get_selection()
        unused, rows = selection.get_selected_rows()

        self.move(rows[0][0], self.current_tab_id, dest_list)

    def _show_information(self, widget):
        # Private.  Get the ID and image of the anime and show the information window.

        selection = self.treeview[self.current_tab_id].get_selection()
        row = selection.get_selected_rows()[1][0][0]
        anime_id = int(self.liststore[self.current_tab_id][row][0])
        image_url = self.data[anime_id]['image']

        self.show_information_window(anime_id, image_url)

    def _copy_anime_title(self, widget):
        # Private.  Copy the title of the anime to the clipboard.

        selection = self.treeview[self.current_tab_id].get_selection()
        row = selection.get_selected_rows()[1][0][0]
        anime_title = self.liststore[self.current_tab_id][row][2]

        self.al.clipboard.set_text(anime_title)

    # List display/edit functions

    def fill_lists(self, refresh):
        """Starts get_data in a thread and add_rows when the thread is finished to fill the lists with data."""

        def get_data(refresh):
            # Get data from cache or download it from MAL and save it to the local cache.

            filename = '%s/%s_animelist.cpickle' % (self.al.HOME, self.al.config.settings['username'])

            if refresh == False:
                if os.path.exists(filename):
                    self.data = utils.get_cache(filename)
                    if self.data is None:
                        refresh = True
                else:
                    refresh = True

            if refresh:
                self.data = self.al.mal.anime.list()
                utils.cache_data(filename, self.data)

        def add_rows():
            # Add all anime data to the lists.

            for k, v in enumerate(self.al.config.anime['status']):
                self.liststore[k].clear()

            if self.data is None or not self.data:
                self.al.gui['statusbar'].update('Anime: Could not refresh/update the data.')
                return

            if isinstance(self.data, dict):
                for k, v in self.data.iteritems():
                    self.liststore[self.al.config.anime['rstatus'][v['watched_status']]].append((
                        v['id'],    # Anime ID (hidden)
                        None,       # Status
                        v['title'], # Title
                        v['type'],  # Type
                        None,       # Progress (watched episodes/episodes)
                        v['score']  # Score
                        ))

            self._update_item_count()

            self.al.signal.emit('al-plugin-signal-1')
            self.al.gui['statusbar'].clear(1000)

        self.al.gui['statusbar'].update('Anime: Loading data...')

        t = gthreads.AsyncTask(get_data, add_rows)
        t.start(refresh)

    def refresh(self, widget=None):
        """Wrapper for fill_lists."""

        self.fill_lists(True)

    def _cell_status_display(self, column, cell, model, iter):
        # Private.  Set background for status column.

        anime_id = model.get_value(iter, 0)
        status = self.data[anime_id]['status']

        cell.set_property('background-gdk', self.al.config.anime['cstatus'][status])

    def _cell_progress_display(self, column, cell, model, iter):
        # Private.  Put 'watched episodes/episodes' in column.

        anime_id = model.get_value(iter, 0)
        episodes = self.data[anime_id]['episodes']
        if episodes == 0: episodes = '?'

        cell.set_property('text', '%s/%s' % (self.data[anime_id]['watched_episodes'], episodes))

    def _cell_progress_start_edit(self, cellrenderer, editable, row, list_id):
        # Private.  Split the episodes from the watched episodes.

        editable.set_text(editable.get_text().split('/', 1)[0])

    def _create_columns(self, treeview, list_id):
        # Private.  Create columns.

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
        column.set_cell_data_func(renderer, self._cell_status_display)
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
        renderer.connect('editing-started', self._cell_progress_start_edit, list_id)
        renderer.connect('edited', self._cell_progress_edited, list_id)
        column = gtk.TreeViewColumn('Progress', renderer, text=4)
        column.set_sort_column_id(4)
        column.set_cell_data_func(renderer, self._cell_progress_display)
        treeview.append_column(column)

        # Score
        renderer = gtk.CellRendererSpin()
        renderer.set_property('editable', True)
        adjustment = gtk.Adjustment(0, 0, 10, 1)
        renderer.set_property('adjustment', adjustment)
        renderer.connect('edited', self._cell_score_edited, list_id)
        column = gtk.TreeViewColumn('Score', renderer, text=5)
        column.set_sort_column_id(5)
        treeview.append_column(column)

    def _sort_progess(self, model, iter1, iter2, data=None):
        # Private.  Sort the list by progress (total episodes).

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

    def _cell_progress_edited(self, cellrenderer, row, new_progress, list_id):
        # Private.  Validate given progress and update score cell, local cache and MAL.

        anime_id = int(self.liststore[list_id][row][0])
        old_progress = self.data[anime_id]['watched_episodes']
        new_progress = int(new_progress)

        if new_progress != old_progress:

            self.al.gui['statusbar'].update('Anime: Sending changes to MyAnimeList...')

            episodes = self.data[anime_id]['episodes']
            if episodes == 0: episodes = '?'

            # This isn't needed because _cell_progress_display already does this
            # self.liststore[list_id][row][4] = '%s/%s' % (new_progress, episodes)
            self.data[anime_id]['watched_episodes'] = new_progress

            # Update MAL
            t = gthreads.AsyncTask(self.al.mal.anime.update, self._clear_message)
            t.start(
                anime_id,
                {'status': self.data[anime_id]['watched_status'],
                'episodes': self.data[anime_id]['watched_episodes'],
                'score': self.data[anime_id]['score']})

    def _cell_score_edited(self, cellrenderer, row, new_score, list_id):
        # Private.  Validate given score and update score cell, local cache and MAL.

        anime_id = self.liststore[list_id][row][0]
        old_score = self.liststore[list_id][row][5]
        new_score = int(new_score)

        if new_score != old_score and new_score >= 0 and new_score <= 10:

            self.al.gui['statusbar'].update('Anime: Sending changes to MyAnimeList...')

            self.liststore[list_id][row][5] = new_score
            self.data[anime_id]['score'] = new_score

            # Update MAL
            t = gthreads.AsyncTask(self.al.mal.anime.update, self._clear_message)
            t.start(
                anime_id,
                {'status': self.data[anime_id]['watched_status'],
                'episodes': self.data[anime_id]['watched_episodes'],
                'score': self.data[anime_id]['score']})

    # Functions for adding, removing and updating anime

    # Note:
    #  - All these functions are meant for internal use (usage in this class).
    #    Except for 'add', which is used to add anime from the search section.

    def add(self, params):
        """Prepend a row to a list."""

        def callback(result):
            self._clear_message(result)
            self._update_item_count()

        self.al.gui['statusbar'].update('Anime: Sending changes to MyAnimeList...')

        self.data[int(params['id'])] = {
            'id':               params['id'],
            'title':            params['title'],
            'type':             params['type'],
            'episodes':         params['episodes'],
            'status':           params['status'],
            'watched_status':   params['watched_status'],
            'watched_episodes': params['watched_episodes'],
            'score':            params['score'],
            'image':            params['image']
            }

        list_data = (params['id'], None, params['title'], params['type'], None, params['score'])
        self.liststore[self.al.config.anime['rstatus'][params['watched_status']]].insert(0, list_data)

        add_params = {
            'anime_id': params['id'],
            'status':   params['watched_status'],
            'score':    params['score']
            }

        if params['watched_status'] == 'completed':
            add_params['episodes'] = params['watched_episodes']

        t = gthreads.AsyncTask(self.al.mal.anime.add, callback)
        t.start(add_params)

    def delete(self):
        """Removes the selected row from the list."""

        def callback(result):
            self._clear_message(result)
            self._update_item_count()

        self.al.gui['statusbar'].update('Anime: Sending changes to MyAnimeList...')

        # Get anime ID and list iter
        selection = self.treeview[self.current_tab_id].get_selection()
        row = selection.get_selected_rows()[1][0][0]
        iter = selection.get_selected()[1]
        anime_id = self.liststore[self.current_tab_id][row][0]

        # Remove anime from list and cache
        self.liststore[self.current_tab_id].remove(iter)
        del self.data[anime_id]

        # Start thread
        t = gthreads.AsyncTask(self.al.mal.anime.delete, callback)
        t.start(anime_id)

    def move(self, row, current_list, dest_list):
        """Move a row to an other list."""

        def callback(result):
            self._clear_message(result)
            self._update_item_count()

        self.al.gui['statusbar'].update('Anime: Sending changes to MyAnimeList...')

        anime_id = self.liststore[current_list][row][0]

        # Update local cache
        self.data[anime_id]['watched_status'] = self.al.config.anime['status'][dest_list]
        self.liststore[dest_list].insert(0, self.liststore[current_list][row])

        iter = self.liststore[current_list].get_iter(row)
        self.liststore[current_list].remove(iter)

        # Start thread
        t = gthreads.AsyncTask(self.al.mal.anime.update, callback)
        t.start(
            anime_id,
            {'status': self.data[anime_id]['watched_status'],
            'episodes': self.data[anime_id]['watched_episodes'],
            'score': self.data[anime_id]['score']})

class InfoWindow(gtk.Builder):

    def __init__(self, ui_file):

        gtk.Builder.__init__(self)
        self.add_from_file(ui_file)

        self.gui = {
            'window': self.get_object('info_window'),
            'image': self.get_object('iw_image'),
            'mal_button': self.get_object('iw_mal_button'),
            'title': self.get_object('iw_title'),
            'synopsis': self.get_object('iw_synopsis'),
            'other_titles_box': self.get_object('iw_other_titles_box'),
            'other_titles_content': self.get_object('iw_other_titles_content'),
            'related_box': self.get_object('iw_related_box'),
            'related_content': self.get_object('iw_related_content'),
            'info_content': self.get_object('iw_info_content'),
            'stats_content': self.get_object('iw_stats_content')
            }

        self.mal_url = None
        self.gui['window'].connect('key-release-event', self._handle_key)
        self.gui['mal_button'].connect('clicked', self._on_click)

    def set_info(self, data):
        """Format all the data and add it to all the labels."""

        self.gui['window'].show_all()

        self.gui['window'].set_title(data['title'])
        self.gui['title'].set_markup('<span size="x-large" font_weight="bold">%s</span>' % data['title'])
        data['synopsis'] = utils.strip_html_tags(data['synopsis'].replace('<br>', '\n'))
        self.gui['synopsis'].set_label(data['synopsis'])
        self.mal_url = 'http://myanimelist.net/anime/%d' % data['id']

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
            self.gui['related_content'].set_markup('<span size="small">%s</span>' % '\n'.join(markup))
        else:
            self.gui['related_box'].hide()

        # Other titles
        markup = []

        for k, v in data['other_titles'].iteritems():
            for s in v:
                markup.append('<b>%s:</b> %s' % (k.capitalize(), s))

        if len(markup) > 0:
            self.gui['other_titles_content'].set_markup('<span size="small">%s</span>' % '\n'.join(markup))
        else:
            self.gui['other_titles_box'].hide()

        # Information
        markup = (
            '<b>Type:</b> %s' % data['type'],
            '<b>Episodes:</b> %s' % data['episodes'],
            '<b>Status:</b> %s' % data['status'].capitalize(),
            '<b>Genres:</b> %s' % ', '.join(data['genres']),
            '<b>Classification:</b> %s' % data['classification'].replace('&', '&amp;')
            )
        self.gui['info_content'].set_markup('<span size="small">%s</span>' % '\n'.join(markup))

        # Statistics
        markup = (
            '<b>Score:</b> %s' % data['members_score'],
            '<b>Ranked:</b> #%s' % data['rank'],
            '<b>Popularity:</b> #%s' % data['popularity_rank'],
            '<b>Members:</b> %s' % data['members_count'],
            '<b>Favorites:</b> %s' % data['favorited_count']
            )
        self.gui['stats_content'].set_markup('<span size="small">%s</span>' % '\n'.join(markup))

    def set_image(self, image):
        """Set the image."""

        self.gui['image'].clear()
        self.gui['image'].set_from_file(image)

    def _handle_key(self, widget, event):
        # Private.  Handle key events of widgets.

        string, state = event.string, event.state
        keyname =  gtk.gdk.keyval_name(event.keyval)

        if keyname == 'Escape':
            self.gui['window'].destroy()

    def _on_click(self, button):

        if self.mal_url is None:
            return

        webbrowser.open(self.mal_url)
