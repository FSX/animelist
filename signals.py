#!/usr/bin/python

# =============================================================================
# signals.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gobject

class Signals(gobject.GObject):
    __gsignals__ = {
        'al-startup' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'al-shutdown' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'al-gui-done' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'al-pref-reset' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'al-user-set' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'al-no-user-set' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
        }

    def __init__(self):
        gobject.GObject.__init__(self)

gobject.type_register(Signals)
