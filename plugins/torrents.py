#!/usr/bin/python

# =============================================================================
# plugins/torrent.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import urllib2
import xml.etree.cElementTree as et

import gtk

from plugin import BasePlugin
from lib.pygtkhelpers import gthreads

class Plugin(BasePlugin):

    plugin_data = {
        'name': 'torrents',
        'fancyname': 'Torrents',
        'version': '0.1',
        'description': '''Adds a torrent section, which downloads RSS/Atom
feeds from certain websites and shows the items that are in the watching list.'''
        }

    def __init__(self, al):
        BasePlugin.__init__(self, al)

    def _load_plugin(self):

        # Toolbar button
        self.al.gui['toolbar'].insert(self.plugin_data['fancyname'], 3)

        # GUI
        self.box = gtk.VBox()

        # Torrents list
        self.liststore = gtk.ListStore(str, str, str, str, str)
        ls_sort = gtk.TreeModelSort(self.liststore)
        ls_sort.set_sort_column_id(4, gtk.SORT_DESCENDING)

        self.treeview = gtk.TreeView(ls_sort)
        self.treeview.set_rules_hint(True)
        self.treeview.set_search_column(3)
        self.treeview.set_tooltip_column(3)
        self.treeview.columns_autosize()

        self.__create_columns()

        # Create scrollbox
        frame = gtk.ScrolledWindow()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        frame.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Pack it together
        frame.add(self.treeview)
        self.box.pack_start(frame)
        self.al.gui['box'].pack_start(self.box)

        # Events
        self.al.signal.connect('al-switch-section', self.__switch_section)

        # Load data
        self.__fill_list()

    def __switch_section(self, signal, section_name):

        if section_name == self.plugin_data['fancyname']:
            self.box.show()
        else:
            self.box.hide()

    # List view functions

    def __fill_list(self):

        def get_data(func):
            return func()

        def add_rows(feed_name, data):

            if data == False:
                return

            for v in data:
                self.liststore.append((
                    None,
                    feed_name,
                    v['url'],
                    v['title'],
                    v['date']
                    ))

        # Start threads for fetching data
        for func in (animesuki_rss_parser, tokyo_toshokan_rss_parser):
            t = gthreads.AsyncTask(get_data, add_rows)
            t.start(func)

    def __create_columns(self):
        "Create columns."

        # Anime ID (not yet used)
        column = gtk.TreeViewColumn(None, None)
        column.set_visible(False)
        self.treeview.append_column(column)

        # Feed name
        column = gtk.TreeViewColumn(None, None)
        column.set_visible(False)
        self.treeview.append_column(column)

        # Url (to torrent or description website)
        column = gtk.TreeViewColumn(None, None)
        column.set_visible(False)
        self.treeview.append_column(column)

        # Title
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Title', renderer, text=3)
        column.set_sort_column_id(3)
        column.set_resizable(True)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_expand(True)
        #column.set_cell_data_func(renderer, self.__cell_title_display)
        self.treeview.append_column(column)

        # Date
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Date', renderer, text=4)
        column.set_sort_column_id(4)
        self.treeview.append_column(column)

# The TokyoToshokanRssParser, AnimeSukiRssParser and BakaBtRssParser functions
# are used to fetch, parse and prepare the data for the GUI.

def fetch_items(url):
    "Fetches an RSS feed and returns the items in a dict."

    try:
        xmlfile = urllib2.urlopen(url)
    except urllib2.URLError:
        print 'Torrents plugin: %s' % urllib2.URLError.reason
        return False

    data = []
    tree = et.parse(xmlfile)
    items = tree.getiterator('item')

    for i in items:
        children = i.getchildren()
        data_set = {}

        for c in children:
            data_set[c.tag] = unicode(c.text)

        data.append(data_set)

    return data

def animesuki_rss_parser():
    """RSS feed parser for AnimeSuki.

       Url: http://animesuki.com/
       Feed: http://www.animesuki.com/rss.php
       """

    items = fetch_items('http://www.animesuki.com/rss.php')
    data = []

    for item in items:
        data.append({
            'title': item['title'].replace('&', '&amp;'), # GTK gives an error about an & without this
            'url': item['link'],
            'date': item['pubDate']
            })

    return ('animesuki', data)

def tokyo_toshokan_rss_parser():
    """RSS feed parser for Tokyo Toshokan.

       Url: http://www.tokyotosho.info/
       Feed: http://tokyotosho.info/rss.php
       """

    items = fetch_items('http://tokyotosho.info/rss.php')
    data = []

    for item in items:
        if item['category'] == 'Anime':
            data.append({
                'title': item['title'],
                'url': item['link'],
                'date': item['pubDate']
                })

    return ('tokyotosho', data)

def bakabt_rss_parser():
    """RSS feed parser for BakaBT.

       Only power users can use the RSS feed from BakaBT.
       There'll be a GUI to set the feed url.

       Url: http://www.bakabt.com/
       """

    pass























