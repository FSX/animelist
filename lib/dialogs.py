#!/usr/bin/python

# =============================================================================
# lib/dialogs.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gtk

def about(name, version, copyright, comments, website, icon):
    "Shows an about dialog."

    about = gtk.AboutDialog()
    about.set_program_name(name)
    about.set_version(version)
    about.set_copyright(copyright)
    about.set_comments(comments)
    about.set_website(website)
    about.set_logo(icon)
    about.run()
    about.destroy()
