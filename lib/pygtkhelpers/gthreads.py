#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    :copyright: 2005-2008 by The PIDA Project
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""

# Note: This module/file has been modified and is not the same as the original
#       module/file from the pygtkhelpers library. Go to
#       http://bitbucket.org/aafshar/pygtkhelpers-main/ for the original file.

import threading
import gobject

class AsyncTask(object):
    """
    AsyncTask is used to help you perform lengthy tasks without delaying
    the UI loop cycle, causing the app to look frozen. It is also assumed
    that each action that the async worker performs cancels the old one (if
    it's still working), thus there's no problem when the task takes too long.
    You can either extend this class or pass two callable objects through its
    constructor.

    The first on is the 'work_callback' this is where the lengthy
    operation must be performed. This object may return an object or a group
    of objects, these will be passed onto the second callback 'loop_callback'.
    You must be aware on how the argument passing is done. If you return an
    object that is not a tuple then it's passed directly to the loop callback.
    If you return `None` no arguments are supplied. If you return a tuple
    object then these will be the arguments sent to the loop callback.

    The loop callback is called inside Gtk+'s main loop and it's where you
    should stick code that affects the UI.
    """
    def __init__(self, work_callback=None, loop_callback=None, daemon=True):
        self.counter = 0
        gobject.threads_init() #the glib mainloop doesn't love us else
        self.daemon = daemon

        if work_callback is not None:
            self.work_callback = work_callback
        if loop_callback is not None:
            self.loop_callback = loop_callback

    def start(self, *args, **kwargs):
        """
        * not threadsave
        * assumed to be called in the gtk mainloop
        """
        args = (self.counter,) + args
        thread = threading.Thread(
                target=self._work_callback,
                args=args, kwargs=kwargs
                )
        thread.setDaemon(self.daemon)
        thread.start()

    def work_callback(self):
        pass

    def loop_callback(self):
        pass

    def _work_callback(self, counter, *args, **kwargs):
        ret = self.work_callback(*args, **kwargs)
        #tuple necessary cause idle_add wont allow more args
        gobject.idle_add(self._loop_callback, (counter, ret))

    def _loop_callback(self, vargs):
        counter, ret = vargs
        if counter != self.counter:
            return

        if ret is None:
            ret = ()
        if not isinstance(ret, tuple):
            ret = (ret,)

        self.loop_callback(*ret)
