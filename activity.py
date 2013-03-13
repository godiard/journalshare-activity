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

import logging
from threading import Thread

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import WebKit

from sugar3.activity import activity
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3 import network


class JournalHTTPRequestHandler(network.ChunkedGlibHTTPRequestHandler):
    """HTTP Request Handler to send data to the webview.

    RequestHandler class that integrates with Glib mainloop. It writes
    the specified file to the client in chunks, returning control to the
    mainloop between chunks.

    """
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        """Respond to a GET request."""
        logging.error('inside do_get dir(self) %s', dir(self))
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("<html><head><title>Title goes here.</title></head>")
        self.wfile.write("<body><p>This is a test.</p>")
        # If someone went to "http://something.somewhere.net/foo/bar/",
        # then s.path equals "/foo/bar/".

        #self.wfile.write("<p>You accessed path: %s</p>" % self.path)
        self.wfile.write("</body></html>")


class JournalHTTPServer(network.GlibTCPServer):
    """HTTP Server for transferring document while collaborating."""

    def __init__(self, server_address):
        """Set up the GlibTCPServer with the JournalHTTPRequestHandler.
        """
        network.GlibTCPServer.__init__(self, server_address,
                                       JournalHTTPRequestHandler)


class JournalShare(activity.Activity):

    def __init__(self, handle):

        activity.Activity.__init__(self, handle)

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

        activity_path = activity.get_bundle_path()
        self.view = WebKit.WebView()
        #self.view.load_uri('file://%s/web/index.html' % activity_path)
        self.view.load_uri('http://localhost:2500')
        self.view.show()
        self.set_canvas(self.view)

        # TODO: set the port in a more inteligent way
        self.port = 2500
        self._server = JournalHTTPServer(("", self.port))
        server = Thread(target=self._server.serve_forever)
        server.setDaemon(True)
        logging.debug("Before start server")
        server.start()
        logging.debug("After start server")

    def read_file(self, file_path):
        pass

    def write_file(self, file_path):
        pass

    def can_close(self):
        self._server.shutdown()
        return True
