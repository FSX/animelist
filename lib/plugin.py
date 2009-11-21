#!/usr/bin/python

# =============================================================================
# plugin.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import sys

class BasePlugin(object):

    def __init__(self, al):
        self.al = al
        self._load_plugin()

    def _load_plugin(self):
        pass

    def _unload_plugin(self):
        pass

class PluginSys():

    _instances = {}

    def __init__(self, al, config):
        "Adds the plugin directory to the import path and loads the plugin."

        self.al = al

        if not config['plugin_path'] in sys.path:
            sys.path.insert(0, config['plugin_path'])

        self.load(config['plugins'])

    def load(self, plugins):
        "Load a set of plugins and start the loaded plugins."

        for plugin in plugins:
            __import__(plugin, None, None, [''])
            self._instances[plugin] = sys.modules[plugin].Plugin(self.al)

    def unload(self, plugins):
        "Run the unload function and delete the instance of the plugin."

        for plugin in plugins:
            self._instances[plugin]._unload_plugin()
            del self._instances[plugin]

    def find(self):
        "Returns the subclasses of the BasePlugin."

        return BasePlugin.__subclasses__()

    def list(self):
        "Returns the data of all the plugins in a set."

        plugin_list = []

        for plugin in self._instances:
            plugin_list.append(self._instances[plugin].plugin_data)

        return plugin_list
