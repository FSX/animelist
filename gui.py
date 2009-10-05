#!/usr/bin/python

# =============================================================================
# gui.py
#
# Copyright (c) 2009 Frank Smit (FSX)
# License: GPL v3, see the COPYING file for details
# =============================================================================

import gtk
import gobject

from lib import utils
from lib.dialogs import about_dialog

class Window(gtk.Window):

    def __init__(self, al):

        self.al = al
        gtk.Window.__init__(self)

        # Create window
        self.set_gravity(gtk.gdk.GRAVITY_NORTH_WEST)
        self.set_title(self.al.name)
        self.set_icon(utils.get_image('./pixmaps/animelist_logo_32.png'))
        self._position = (0, 0) # Stores the position of the window. Starts with an
                                # underscore, because 'position' is already taken.

        if self.al.config.settings['position']['maximized'] == True:
            self.maximize()

        if self.al.config.settings['position']['x'] is not None:
            self.move(self.al.config.settings['position']['x'], self.al.config.settings['position']['y'])
        else:
            self.set_position(gtk.WIN_POS_CENTER)

        self.set_default_size(self.al.config.settings['position']['width'], self.al.config.settings['position']['height'])

        # Events
        self.al.signal.connect('al-shutdown-lvl1', self.__set_position_settings)
        self.connect('window-state-event', self.__state_changed)
        self.connect('configure-event', self.__store_position)
        self.connect('destroy', self.al.quit)

    def __set_position_settings(self, widget):
        "Save the position and the dimensions of the window in the settings."

        # Only save the position and dimensions when the window is not maximized
        if self.al.config.settings['position']['maximized'] == False:
            self.al.config.settings['position']['x'] = self._position[0]
            self.al.config.settings['position']['y'] = self._position[1]
            (self.al.config.settings['position']['width'], self.al.config.settings['position']['height']) = self.get_size()

    def __state_changed(self, widget, event):
        """A callback connected to the window's window-state-event signal. This
        is used to keep track of whether the window is maximized or not."""

        if event.new_window_state == gtk.gdk.WINDOW_STATE_MAXIMIZED:
            self.al.config.settings['position']['maximized'] = True
        else:
            self.al.config.settings['position']['maximized'] = False

    def __store_position(self, event, position):
        "Store the position of the window when it's moved or resized."

        self._position = (position.x, position.y)

class Toolbar(gtk.Toolbar):

    def __init__(self, al):

        self.al = al
        gtk.Toolbar.__init__(self)
        self.set_style(gtk.TOOLBAR_ICONS)

        # Buttons
        self.buttons = {}
        self.__generate_buttons(self, self.buttons, (
            ('refresh', {
                'stock': gtk.STOCK_REFRESH,
                'event': ('clicked', self.__on_refresh),
                'tooltip': 'Refresh anime list'
                }),
            ('save', {
                'stock': gtk.STOCK_SAVE,
                'event': ('clicked', self.__on_save),
                'tooltip': 'Save anime list to cache'
                }),
            'separator',
            ('anime', {
                'icon': './pixmaps/monitor.png',
                'event': ('clicked', self.__on_anime),
                'tooltip': 'Go to your anime list'
                }),
            ('search', {
                'stock': gtk.STOCK_FIND,
                'event': ('clicked', self.__on_search),
                'tooltip': 'Go to the search section'
                }),
            'separator',
            ('preferences', {
                'stock': gtk.STOCK_PREFERENCES,
                'event': ('clicked', self.__on_prefs),
                'tooltip': 'Show the preferences dialog'
                }),
            'separator',
            ('about', {
                'stock': gtk.STOCK_ABOUT,
                'event': ('clicked', self.__on_about),
                'tooltip': 'Show about dialog'
                }),
            ('quit', {
                'stock': gtk.STOCK_QUIT,
                'event': ('clicked', self.al.quit),
                'tooltip': 'Quit'
                })
            ))

        # Events
        self.al.signal.connect('al-user-set', self.__enable_control)
        self.al.signal.connect('al-no-user-set', self.__disable_control)
        self.al.signal.connect('al-init-done', self.__init_done)

    # Misc functions

    def __enable_control(self, widget=None):
        "Enable buttons when a user has been set."

        if self.al.current_section == 1:
            self.buttons['refresh'].set_sensitive(True)
            self.buttons['save'].set_sensitive(True)
            self.buttons['anime'].set_sensitive(False)
            self.buttons['search'].set_sensitive(True)

        if self.al.current_section == 2:
            self.buttons['anime'].set_sensitive(True)
            self.buttons['search'].set_sensitive(False)

    def __disable_control(self, widget=None):
        "Disable buttons when no user has been set."

        self.buttons['refresh'].set_sensitive(False)
        self.buttons['save'].set_sensitive(False)
        self.buttons['anime'].set_sensitive(False)
        self.buttons['search'].set_sensitive(False)

    def __init_done(self, widget=None):

        # Disable anime button
        self.buttons['anime'].set_sensitive(False)

    def __generate_buttons(self, toolbar, buttons, data):
        "Generate the buttons for a toolbar."

        for i, v in enumerate(data):

            if v == 'separator':
                toolbar.insert(gtk.SeparatorToolItem(), i)
                continue

            if 'stock' in v[1]:
                toolbar.buttons[v[0]] = gtk.ToolButton(v[1]['stock'])
            else:
                toolbar.buttons[v[0]] = gtk.ToolButton()

            if 'icon' in v[1]:
                image = gtk.Image()
                image.set_from_icon_set(gtk.IconSet(gtk.gdk.pixbuf_new_from_file(v[1]['icon'])), gtk.ICON_SIZE_SMALL_TOOLBAR)
                toolbar.buttons[v[0]].set_icon_widget(image)

            toolbar.buttons[v[0]].connect(v[1]['event'][0], v[1]['event'][1])
            toolbar.buttons[v[0]].set_tooltip_text(v[1]['tooltip'])

            toolbar.insert(toolbar.buttons[v[0]], i)

    # Widget callbacks

    def __on_refresh(self, widget):
        self.al.anime.refresh()

    def __on_save(self, widget):
        self.al.anime.save()

    def __on_prefs(self, widget):
        Preferences(self.al)

    def __on_anime(self, widget):
        self.buttons['refresh'].set_sensitive(True)
        self.buttons['save'].set_sensitive(True)
        self.buttons['search'].set_sensitive(True)
        self.buttons['anime'].set_sensitive(False)
        self.al.switch_section(1)

    def __on_search(self, widget):
        self.buttons['anime'].set_sensitive(True)
        self.buttons['refresh'].set_sensitive(False)
        self.buttons['save'].set_sensitive(False)
        self.buttons['search'].set_sensitive(False)
        self.al.switch_section(2)

    def __on_about(self, widget):
        about_dialog(
            self.al.name,
            self.al.version,
            'Copyright (c) 2009 Frank Smit',
            'MyAnimeList.net anime list manager + some extra stuff.',
            'http://61924.nl',
            utils.get_image('./pixmaps/animelist_logo_256.png')
            )

class Statusbar(gtk.Statusbar):

    def __init__(self, al):

        # self.al = al # Is not needed in this class
        gtk.Statusbar.__init__(self)
        self.statusbar_message_id = None

    def update(self, text):
        "Set/Update/Change statusbar text."

        if not self.statusbar_message_id is None:
            self.remove(0, self.statusbar_message_id)

        self.statusbar_message_id = self.push(0, text)

    def clear(self, remove_timeout=None):
        "Clear statusbar."

        if not self.statusbar_message_id is None:
            if not remove_timeout is None:
                gobject.timeout_add(remove_timeout, self.remove, 0,
                    self.statusbar_message_id)
            else:
                self.remove(0, self.statusbar_message_id)

class Systray(gtk.StatusIcon):

    def __init__(self, al):

        self.al = al
        gtk.StatusIcon.__init__(self)

        self.set_from_pixbuf(utils.get_image('./pixmaps/animelist_logo_32.png'))
        self.connect('activate', self.__activate_icon)
        self.set_visible(True)

    def __activate_icon(self, widget, data=None):
        "Hide and show the main window."

        if self.al.window.get_property('visible'):
            self.al.window.hide()
        else:
            self.al.window.move(self.al.window._position[0], self.al.window._position[1])
            self.al.window.show()
            self.al.window.present()

class Preferences(gtk.Dialog):
    """Preferences dialog, saves al settings when OK is pressed and discards all
       changes when Cancel is pressed."""

    def __init__(self, al):

        self.al = al

        # Field (entry, checknutton) objects are saved in this variable
        self.fields = {}

        # Objects (fields, text, frames) that are displayed in the prefs dialog
        objects = (
            self.__generate_box(
                'User details', {
                    'username': ('Username', 'entry'),
                    'password': ('Password', 'secret_entry')}),
            self.__generate_box(
                'Options', {
                    'startup_refresh': (
                        'Sync list with MyAnimeList on startup',
                        'checkbox'),
                    'systray': (
                        'Enable system tray icon *',
                        'checkbox'),
                        })
            )

        # Dialog
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)

        gtk.Dialog.__init__(self, 'Preferences', self.al.window, flags, buttons)
        self.set_default_response(gtk.RESPONSE_ACCEPT)

        # Table
        table = gtk.Table(len(objects), 1)
        table.set_border_width(5)
        table.set_row_spacings(10)

        for i, obj in enumerate(objects):
            table.attach(obj, 0, 1, i, i+1)

        table.show_all()
        self.vbox.pack_start(table, False, True)

        # Check and save all preferences/settings
        # All preferences are first stored in a temperary variable to check if the
        # preferences have been changed.
        if self.run() == gtk.RESPONSE_ACCEPT:

            tmp_settings = {}

            # Get data from all entries/checkboxes and store it in `tmp_settings`
            for field_id, widget in self.fields.iteritems():

                widget_type = widget.get_name()

                if widget_type == 'GtkEntry':
                    tmp_settings[field_id] = widget.get_text()
                elif widget_type == 'GtkCheckButton':
                    tmp_settings[field_id] = widget.get_active()

            # Check if user details are entered
            if len(tmp_settings['username']) > 0 and len(tmp_settings['password']) > 0:
                self.al.signal.emit('al-user-set')

                # Only send a signal when the user details have been changed
                if tmp_settings['username'] != self.al.config.settings['username'] and \
                   tmp_settings['password'] != self.al.config.settings['password']:
                    self.al.signal.emit('al-user-details-changed')
            else:
                self.al.signal.emit('al-no-user-set')

            # Save settings
            for k in tmp_settings:
                self.al.config.settings[k] = tmp_settings[k]

            #self.al.config.__save_settings()

        self.destroy()

    def __generate_box(self, name, fields):
        """Generates frames with fields in it. All field objects are saved in self.fields (dict).
           Note: only support for gtk.Entry and gtk.CheckButton at this moment."""

        count = 0
        frame = gtk.Frame(name)
        table = gtk.Table(2, 2)
        table.set_border_width(10)
        table.set_row_spacings(5)
        table.set_col_spacings(5)

        for field_id, field in fields.iteritems():

            # Text entry
            if field[1] == 'entry' or field[1] == 'secret_entry':
                self.fields[field_id] = gtk.Entry()

                if field[1] == 'secret_entry':
                    self.fields[field_id].set_visibility(False)

                if field_id in self.al.config.settings:
                    self.fields[field_id].set_text(self.al.config.settings[field_id])

                table.attach(gtk.Label(field[0]), 0, 1, count, count+1)
                table.attach(self.fields[field_id], 1, 2, count, count+1)

            # Checkbox
            elif field[1] == 'checkbox':
                self.fields[field_id] = gtk.CheckButton(field[0])

                if field_id in self.al.config.settings and self.al.config.settings[field_id] == True:
                    self.fields[field_id].set_active(True)

                table.attach(self.fields[field_id], 0, 1, count, count+1)

            count += 1

        frame.add(table)

        return frame
