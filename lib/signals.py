# =============================================================================
# lib/signals.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gobject

class Signals(gobject.GObject):
    __gsignals__ = {

        # Connect to this signal if you have to set configuration variables
        'al-shutdown-lvl1': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),

        # Connect to this signal if you have to save the settings/configuration
        'al-shutdown-lvl2': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),

        'al-init-done': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'al-pref-reset': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'al-block-acess': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'al-unblock-access': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'al-user-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'al-user-verified': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),

        # Emitted after the plugins have been initiated
        'al-plugin-init-done': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),

        'al-plugin-signal-1': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'al-switch-section': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
        }

    def __init__(self):
        gobject.GObject.__init__(self)

gobject.type_register(Signals)
