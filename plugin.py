#!/usr/bin/python

# =============================================================================
# plugin.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import sys
import os

class BasePlugin(object):

    def _load_plugin(self):
        pass

    def _unload_plugin(self):
        pass

class PluginSys():

    _instances = {}

    def __init__(self, al, config):

        self.al = al

        if not config['plugin_path'] in sys.path:
            sys.path.insert(0, config['plugin_path'])

        self.load(config['plugins'])

    def load(self, plugins):

        for plugin in plugins:
            __import__(plugin, None, None, [''])
            self._instances[plugin] = sys.modules[plugin].Plugin(self.al)

    def unload(self, plugins):

        for plugin in plugins:
            self._instances[plugin]._unload_plugin()
            del self._instances[plugin]

    def find(self):

        return BasePlugin.__subclasses__()

    def list(self):

        plugin_list = []

        for plugin in self._instances:
            plugin_list.append(self._instances[plugin].plugin_data)

        return plugin_list
