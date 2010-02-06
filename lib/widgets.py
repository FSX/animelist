# =============================================================================
# lib/widgets.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gtk
import pango
import gobject

from lib import utils

class ToolBar():
    """
    The toolbar holds the buttons that enable the user to navigate between the
    sections.  This class extends gtk.Toolbar and adds extra functionality.
    """

    def __init__(self, al, toolbar):

        self.al = al
        self._toolbar = toolbar
        self.buttons = {}
        self.qeue = []

        self.al.signal.connect('al-init-done', self._insert_buttons)

    def set_section(self, bid=None, label=None):
        """
        Emit a 'al-switch-section' signal when a button on the sections
        toolbar is pressed or when called in the script.  Plugins can connect
        to this signal and do the actual 'section switch'.
        """

        try:
            if bid is not None:
                button = self._toolbar.get_children()[bid]
                label = button.get_label()
            elif label is not None:
                button = self.buttons[label]
        except IndexError:
            return False
        else:
            button.set_sensitive(False)
            self.al.signal.emit('al-switch-section', label)

    def insert(self, label, position=0):
        """Insert a button in the qeue."""

        self.qeue.append((position, label))

    def enable(self, enabled=True):
        """Disable or enable the toolbar."""

        self._toolbar.set_sensitive(enabled)

    def _on_click(self, widget, label):
        # Private.  Called when a button on the sections toolbar is pressed. It makes
        # the clicked button unsensitive and calls `self.set_section`.

        for k in self.buttons:
            if k != label:
                self.buttons[k].set_sensitive(True)

        self.set_section(label=label)

    def _insert_buttons(self, widget=None):
        # Private.  Insert all buttons from the qeue in the toolbar.

        self.qeue.sort()

        for position, label in enumerate(self.qeue):

            label = label[1]

            self.buttons[label] = gtk.ToolButton(label=label)
            self.buttons[label].set_border_width(2)
            self.buttons[label].connect('clicked', self._on_click, label)

            self._toolbar.insert(self.buttons[label], position)

        self.set_section(0)
        self._toolbar.show_all()

class Statusbar():
    """Extends gtk.Statusbar."""

    def __init__(self, al, statusbar):

        self._statusbar = statusbar
        self._statusbar_message_id = None

    def update(self, text):
        """Set/Update/Change statusbar text."""

        # Don't remove the previous text
        #if not self.__statusbar_message_id is None:
        #    self.__statusbar.remove_message(0, self.__statusbar_message_id)

        self._statusbar_message_id = self._statusbar.push(0, text)

    def clear(self, remove_timeout=None):
        """Clear statusbar. With or without a timeout (int)."""

        if not self._statusbar_message_id is None:
            if not remove_timeout is None:
                gobject.timeout_add(remove_timeout, self._statusbar.remove_message, 0,
                    self._statusbar_message_id)
            else:
                self._statusbar.remove_message(0, self._statusbar_message_id)

class SettingsDialog():
    """Spawns a settings dialog and handles the validation of the entered values."""

    def __init__(self, al):

        self.al = al

        # Setup fields
        fields = {
            'username': self.al.builder.get_object('sd_en_username'),
            'password': self.al.builder.get_object('sd_en_password'),
            'systray': self.al.builder.get_object('sd_cb_systray_opt'),
            'startup_refresh': self.al.builder.get_object('sd_cb_startrefresh_opt')
            }

        self._set_fields(fields)

        # Setup dialog
        self.dialog = al.builder.get_object('settings_dialog')
        self.dialog.set_transient_for(self.al.gui['window'])
        self.dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.dialog.show()

        response = self.dialog.run()
        self.dialog.hide()

        # Process/Reset changes
        if response == 1:
            self._set_settings(fields)
        else:
            self._set_fields(fields)

    def _set_fields(self, fields):
        # Private.  Copy the data from self.al.config.settings into all the text fields
        # and checkboxes.

        if self.al.config.settings['username'] is not None:
            fields['username'].set_text(self.al.config.settings['username'])
        else:
            fields['username'].set_text('')

        if self.al.config.settings['password'] is not None:
            fields['password'].set_text(self.al.config.settings['password'])
        else:
            fields['password'].set_text('')

        fields['systray'].set_active(self.al.config.settings['systray'])
        fields['startup_refresh'].set_active(self.al.config.settings['startup_refresh'])

    def _set_settings(self, fields):
        # Private.  Copy all the data from the text fields and checkboxes into
        # self.al.config.settings.

        # Check user details
        user_changed = False

        tmp1 = fields['username'].get_text()
        if tmp1 != self.al.config.settings['username']:
            user_changed = True

        tmp2 = fields['password'].get_text()
        if tmp2 != self.al.config.settings['password']:
            user_changed = True

        # Update settings dict and emit signal when the user details have been changed
        if user_changed == True:
            self.al.config.settings['username'] = tmp1
            self.al.config.settings['password'] = tmp2

            self.al.signal.emit('al-user-changed')

        self.al.config.settings['systray'] = fields['systray'].get_active()
        self.al.config.settings['startup_refresh'] = fields['startup_refresh'].get_active()

        # Show or hide the systemtray icon if needed
        if self.al.config.settings['systray']:
            self.al.gui['systray'].set_visible(True)
        else:
            self.al.gui['systray'].set_visible(False)

class AboutDialog(gtk.AboutDialog):
    """A GTK+ about dialog that displays a description, a link to the website etc."""

    def __init__(self, al):

        gtk.AboutDialog.__init__(self)
        gtk.about_dialog_set_email_hook(self._open_url)
        gtk.about_dialog_set_url_hook(self._open_url)
        self.al = al

        self.set_logo(utils.get_image('%s/pixmaps/animelist_logo_256.png' % al.path))
        self.set_name(al.name)
        self.set_version(al.version)
        self.set_comments('MyAnimeList.net anime list manager + some extra stuff.')
        self.set_copyright('Copyright (c) 2009 Frank Smit')
        self.set_authors(['Frank Smit <61924.00@gmail.com>'])
        self.set_website('http://61924.nl/projects/animelist.html')
        self.set_license(self._read_licence_file())

        self.run()
        self.destroy()

    def _read_licence_file(self):
        # Private.  Get the contents of the license file (COPYING) and return it.

        try:
            #with open('%s/COPYING' % self.al.path, 'r') as f:
            #    contents = f.read()

            fh = open('%s/COPYING' % self.al.path, 'r')
            contents = fh.read()
            fh.close()
        except IOError:
            contents = 'No license file found.'

        return contents

    def _open_url(self, dialog, link, data=None):
        utils.open_url(link)
