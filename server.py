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
import logging
import cgi

import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import SocketServer
import select

from gi.repository import GLib

import utils


class JournalHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler to send data to the webview.

    RequestHandler class that integrates with Glib mainloop. It writes
    the specified file to the client in chunks, returning control to the
    mainloop between chunks.

    """

    def __init__(self, activity_path, activity_root, jm, request,
                 client_address, server):
        self.activity_path = activity_path
        self.activity_root = activity_root
        self.jm = jm
        SimpleHTTPRequestHandler.__init__(self, request, client_address,
                                          server)

    def do_POST(self):
        if self.path == '/datastore/upload':
            ctype = self.headers.get('content-type')
            if not ctype:
                return None
            ctype, pdict = cgi.parse_header(ctype)
            query = cgi.parse_multipart(self.rfile, pdict)

            file_content = query.get('journal_item')[0]
            # save to the journal
            zipped_file_path = os.path.join(self.activity_root,
                                            'instance', 'received.journal')
            f = open(zipped_file_path, 'wb')
            try:
                f.write(file_content)
            finally:
                f.close()

            metadata, preview_data, file_path = \
                utils.unpackage_ds_object(zipped_file_path, None)

            logging.error('METADATA %s', metadata)

            GLib.idle_add(self.jm.create_object, file_path, metadata,
                          preview_data)

            #redirect to index.html page
            self.send_response(301)
            self.send_header('Location', '/web/index.html')
            self.end_headers()

    def do_GET(self):
        """Respond to a GET request."""
        #logging.error('inside do_get dir(self) %s', dir(self))

        if self.path:
            logging.error('Requested path %s', self.path)
            if self.path.startswith('/web'):
                # TODO: check mime_type
                self.send_header_response("text/html")
                # return files requested in the web directory
                file_path = self.activity_path + self.path

                if os.path.isfile(file_path):
                    logging.error('Opening requested file %s', file_path)
                    f = open(file_path)
                    content = f.read()
                    f.close()
                    self.wfile.write(content)

            if self.path.startswith('/datastore'):
                # return files requested in the activity instance directory
                path = self.path.replace('datastore', 'instance')
                file_path = self.activity_root + path

                mime_type = 'text/html'
                if file_path.endswith('.journal'):
                    mime_type = 'application/journal'
                self.send_header_response(mime_type)

                if os.path.isfile(file_path):
                    logging.error('Opening requested file %s', file_path)
                    f = open(file_path)
                    content = f.read()
                    f.close()
                    self.wfile.write(content)

    def send_header_response(self, mime_type, file_name=None):
        self.send_response(200)
        self.send_header("Content-type", mime_type)
        if file_name is not None:
            self.send_header("Content-Disposition",
                             "inline; filename='%s'" % file_name)
        self.end_headers()


class JournalHTTPServer(BaseHTTPServer.HTTPServer):
    """HTTP Server for transferring document while collaborating."""

    # from wikipedia activity
    def serve_forever(self, poll_interval=0.5):
        """Overridden version of BaseServer.serve_forever that does not fail
        to work when EINTR is received.
        """
        self._BaseServer__serving = True
        self._BaseServer__is_shut_down.clear()
        while self._BaseServer__serving:

            # XXX: Consider using another file descriptor or
            # connecting to the socket to wake this up instead of
            # polling. Polling reduces our responsiveness to a
            # shutdown request and wastes cpu at all other times.
            try:
                r, w, e = select.select([self], [], [], poll_interval)
            except select.error, e:
                if e[0] == errno.EINTR:
                    logging.debug("got eintr")
                    continue
                raise
            if r:
                self._handle_request_noblock()
        self._BaseServer__is_shut_down.set()

    def server_bind(self):
        """Override server_bind in HTTPServer to not use
        getfqdn to get the server name because is very slow."""
        SocketServer.TCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = 'localhost'
        self.server_port = port


def run_server(activity_path, activity_root, jm, port):
    # init the journal manager before start the thread
    from threading import Thread
    httpd = JournalHTTPServer(
        ("", port),
        lambda *args: JournalHTTPRequestHandler(activity_path, activity_root,
                                                jm, *args))
    server = Thread(target=httpd.serve_forever)
    server.setDaemon(True)
    logging.debug("Before start server")
    server.start()
    logging.debug("After start server")
