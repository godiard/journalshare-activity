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

import os
import sys
import logging

from gi.repository import Gio
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
        #logging.error('inside do_get dir(self) %s', dir(self))
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # If someone went to "http://something.somewhere.net/foo/bar/",
        # then s.path equals "/foo/bar/".
        # verify if the requested path is in the web_path directory

        file_used = False
        if self.path:
            file_path = self.server.web_path + self.path
            logging.error('Requested file %s', file_path)

            if os.path.isfile(file_path):
                logging.error('Opening requested file %s', file_path)
                f = Gio.File.new_for_path(file_path)
                _error, content, _time = f.load_contents(None)

                logging.error('Closing requested file %s', file_path)
                self.wfile.write(content)
                file_used = True

        if not file_used:
            self.wfile.write("<html><head><title>Title ...</title></head>")
            self.wfile.write("<body><p>This is a test.</p>")
            self.wfile.write("<p>You accessed path: %s</p>" % self.path)
            self.wfile.write("</body></html>")


class JournalHTTPServer(network.GlibTCPServer):
    """HTTP Server for transferring document while collaborating."""

    def __init__(self, server_address, activity_path):
        """Set up the GlibTCPServer with the JournalHTTPRequestHandler.
        """
        self.activity_path = activity_path
        self.web_path = self.activity_path + '/web'
        network.GlibTCPServer.__init__(self, server_address,
                                       JournalHTTPRequestHandler)


class JournalManager():

    def __init__(self):
        pass

    def get_json(self, query):
        """
        Receive a dictionary with the query parameters and creates
        a json with the results
        """
        pass


def setup_server(activity_path):
    # TODO: set the port in a more inteligent way
    port = 2500
    server = JournalHTTPServer(("", port), activity_path)
    return server

if __name__ == "__main__":
    activity_path = sys.argv[1]
    server = setup_server(activity_path)
    try:
        logging.debug("Before start server")
        server.serve_forever()
    except KeyboardInterrupt:
        print "Shutting down server"
        server.shutdown()
