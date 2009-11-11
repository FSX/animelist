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

class Plugin(BasePlugin):

    plugin_data = {
        'name': 'torrents',
        'fancyname': 'Torrents',
        'version': '0.1',
        'description': '''Adds a torrent section, which downloads RSS/Atom
feeds from certain websites and shows the items that are in the watching list.'''
        }

    def __init__(self, al):

        self.al = al
        self._load_plugin()

    def _load_plugin(self):

        # Toolbar button
        self.al.gui['toolbar'].insert(self.plugin_data['fancyname'], 3)

        # GUI
        self.box = gtk.VBox()

        # Torrents list
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
        self.box.pack_start(frame)
        self.al.gui['box'].pack_start(self.box)

        # Events
        self.al.signal.connect('al-switch-section', self.__switch_section)

    def _unload_plugin(self):
        pass

    def __switch_section(self, signal, section_name):

        if section_name == self.plugin_data['fancyname']:
            self.box.show()
        else:
            self.box.hide()

    # List view functions

    def __create_columns(self):
        "Create columns."

        # Anime ID
        column = gtk.TreeViewColumn(None, None)
        column.set_visible(False)
        self.treeview.append_column(column)

        # Website name
        column = gtk.TreeViewColumn(None, None)
        column.set_visible(False)
        self.treeview.append_column(column)

        # Url (to torrent or description website)
        column = gtk.TreeViewColumn(None, None)
        column.set_visible(False)
        self.treeview.append_column(column)

        # Title
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Title', renderer, text=4)
        column.set_sort_column_id(4)
        column.set_resizable(True)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_expand(True)
        #column.set_cell_data_func(renderer, self.__cell_title_display)
        self.treeview.append_column(column)

        # Date
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Date', renderer, text=5)
        column.set_sort_column_id(5)
        self.treeview.append_column(column)

def fetch_items(url):
    "Fetches an RSS feed and returns the items in a dict."

    try:
        xmlfile = urllib2.urlopen(url)
    except urllib2.URLError:
        print 'Torrents (plugin): %s' % urllib2.URLError.reason
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

# The TokyoToshokanRssParser, AnimeSukiRssParser and BakaBtRssParser classes
# are used to fetch, parse and prepare the data for the GUI.

class TokyoToshokanRssParser():
    """RSS feed parser for Tokyo Toshokan.

       Url: http://www.tokyotosho.info/
       Feed: http://www.animesuki.com/rss.php
       """

    def __init__(self):
        pass

class AnimeSukiRssParser():
    """RSS feed parser for AnimeSuki.

       Url: http://animesuki.com/
       Feed: http://tokyotosho.info/rss.php
       """

    def __init__(self):
        pass

class BakaBtRssParser():
    """RSS feed parser for BakaBT.

       Only power users can use the RSS feed from BakaBT.
       There'll be a GUI to set the feed url.

       Url: http://animesuki.com/
       """

    def __init__(self):
        pass
