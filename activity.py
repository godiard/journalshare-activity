# Copyright 2013 Agustin Zubiaga <aguz@sugarlabs.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import subprocess
import logging

from gi.repository import GObject
GObject.threads_init()
from gi.repository import Gtk
from gi.repository import WebKit

import telepathy
import dbus

from sugar3.activity import activity
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbarbox import ToolbarBox

import downloadmanager

JOURNAL_STREAM_SERVICE = 'journal-activity-http'

class JournalShare(activity.Activity):

    def __init__(self, handle):

        activity.Activity.__init__(self, handle)

        activity_path = activity.get_bundle_path()
        #TODO: check available port
        self.port = 2500
        self.server_proc = subprocess.Popen(['/bin/python', 'server.py',
            activity_path, str(self.port)])

        toolbar_box = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        separator.show()
        toolbar_box.toolbar.insert(separator, -1)

        stopbutton = StopButton(self)
        toolbar_box.toolbar.insert(stopbutton, -1)
        stopbutton.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

        self.view = WebKit.WebView()
        self.view.connect('mime-type-policy-decision-requested',
                     self.__mime_type_policy_cb)
        self.view.connect('download-requested', self.__download_requested_cb)

        self.view.load_uri('http://localhost:2500/web/index.html')
        self.view.show()
        self.set_canvas(self.view)

        # collaboration
        self.unused_download_tubes = set()
        self.connect("shared", self._shared_cb)

        if self.shared_activity:
            # We're joining
            if self.get_shared():
                # Already joined for some reason, just connect
                self._joined_cb(self)
            else:
                # Wait for a successful join before trying to connect
                self.connect("joined", self._joined_cb)

    def _joined_cb(self, also_self):
        """Callback for when a shared activity is joined.
        Get the shared tube from another participant.
        """
        self.watch_for_tubes()
        GObject.idle_add(self._get_view_information)

    def _get_view_information(self):
        # Pick an arbitrary tube we can try to connect to the server
        try:
            tube_id = self.unused_download_tubes.pop()
        except (ValueError, KeyError), e:
            logging.error('No tubes to connect from right now: %s',
                          e)
            return False

        GObject.idle_add(self._set_view_url, tube_id)
        return False

    def _set_view_url(self, tube_id):
        chan = self.shared_activity.telepathy_tubes_chan
        iface = chan[telepathy.CHANNEL_TYPE_TUBES]
        addr = iface.AcceptStreamTube(tube_id,
                telepathy.SOCKET_ADDRESS_TYPE_IPV4,
                telepathy.SOCKET_ACCESS_CONTROL_LOCALHOST, 0,
                utf8_strings=True)
        logging.error('Accepted stream tube: listening address is %r', addr)
        # SOCKET_ADDRESS_TYPE_IPV4 is defined to have addresses of type '(sq)'
        assert isinstance(addr, dbus.Struct)
        assert len(addr) == 2
        assert isinstance(addr[0], str)
        assert isinstance(addr[1], (int, long))
        assert addr[1] > 0 and addr[1] < 65536
        port = int(addr[1])

        self.view.load_uri('http://%s:%d/web/index.html' % (addr[0], port))
        return False

    def _start_sharing(self):
        """Share the web server."""

        # Make a tube for the web server
        chan = self.shared_activity.telepathy_tubes_chan
        iface = chan[telepathy.CHANNEL_TYPE_TUBES]
        self._fileserver_tube_id = iface.OfferStreamTube(
                JOURNAL_STREAM_SERVICE, {},
                telepathy.SOCKET_ADDRESS_TYPE_IPV4,
                ('127.0.0.1', dbus.UInt16(self.port)),
                telepathy.SOCKET_ACCESS_CONTROL_LOCALHOST, 0)

    def watch_for_tubes(self):
        """Watch for new tubes."""
        tubes_chan = self.shared_activity.telepathy_tubes_chan

        tubes_chan[telepathy.CHANNEL_TYPE_TUBES].connect_to_signal('NewTube',
            self._new_tube_cb)
        tubes_chan[telepathy.CHANNEL_TYPE_TUBES].ListTubes(
            reply_handler=self._list_tubes_reply_cb,
            error_handler=self._list_tubes_error_cb)

    def _new_tube_cb(self, tube_id, initiator, tube_type, service, params,
                     state):
        """Callback when a new tube becomes available."""
        logging.error('New tube: ID=%d initator=%d type=%d service=%s '
                      'params=%r state=%d', tube_id, initiator, tube_type,
                      service, params, state)
        if service == JOURNAL_STREAM_SERVICE:
            logging.error('I could download from that tube')
            self.unused_download_tubes.add(tube_id)
            GObject.idle_add(self._get_view_information)

    def _list_tubes_reply_cb(self, tubes):
        """Callback when new tubes are available."""
        for tube_info in tubes:
            self._new_tube_cb(*tube_info)

    def _list_tubes_error_cb(self, e):
        """Handle ListTubes error by logging."""
        logging.error('ListTubes() failed: %s', e)

    def _shared_cb(self, activityid):
        """Callback when activity shared.
        Set up to share the document.
        """
        # We initiated this activity and have now shared it, so by
        # definition the server is local.
        logging.error('Activity became shared')
        self.watch_for_tubes()
        self._start_sharing()

    def __mime_type_policy_cb(self, webview, frame, request, mimetype,
                              policy_decision):
        if not self.view.can_show_mime_type(mimetype):
            policy_decision.download()
            return True

        return False

    def __download_requested_cb(self, browser, download):
        downloadmanager.add_download(download, browser)
        return True

    def read_file(self, file_path):
        pass

    def write_file(self, file_path):
        pass

    def can_close(self):
        self.server_proc.kill()
        return True
