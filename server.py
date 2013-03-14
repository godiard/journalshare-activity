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
import json

from gi.repository import Gio
from sugar3 import network
from sugar3.datastore import datastore


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

        file_used = False
        if self.path:
            if self.path.startswith('/web'):
                # TODO: check mime_type
                self.send_header_response("text/html")
                # return files requested in the web directory
                file_path = self.server.activity_path + self.path
                logging.error('Requested file %s', file_path)

                if os.path.isfile(file_path):
                    logging.error('Opening requested file %s', file_path)
                    f = Gio.File.new_for_path(file_path)
                    _error, content, _time = f.load_contents(None)

                    logging.error('Closing requested file %s', file_path)
                    self.wfile.write(content)
                    file_used = True

            if self.path.startswith('/datastore'):
                # queries to the datastore
                jm = JournalManager()
                if self.path == '/datastore/starred':
                    self.send_header_response("text/html")
                    self.wfile.write(jm.get_starred())
                    logging.error('Returned datastore/starred')
                if self.path.startswith('/datastore/id='):
                    object_id = self.path[self.path.find('=') + 1:]
                    mime_type, content = jm.get_object_by_id(object_id)
                    self.send_header_response(mime_type)
                    self.wfile.write(content)

    def send_header_response(self, mime_type):
        self.send_response(200)
        self.send_header("Content-type", mime_type)
        self.end_headers()


class JournalHTTPServer(network.GlibTCPServer):
    """HTTP Server for transferring document while collaborating."""

    def __init__(self, server_address, activity_path):
        """Set up the GlibTCPServer with the JournalHTTPRequestHandler.
        """
        self.activity_path = activity_path
        network.GlibTCPServer.__init__(self, server_address,
                                       JournalHTTPRequestHandler)


class JournalManager():

    def __init__(self):
        pass

    def get_object_by_id(self, object_id):
        dsobj = datastore.get(object_id)
        mime_type = ''
        if 'mime_type' in dsobj.metadata:
            mime_type = dsobj.metadata['mime_type']
        if mime_type == '':
            # TODO: what type should we use if not available?
            mime_type = 'application/x-binary'

        f = open(dsobj.file_path, 'r')
        # TODO: read all the file in memory?
        content = f.read()
        f.close()
        return mime_type, content

    def get_starred(self):
        self.dsobjects, self._nobjects = datastore.find({'keep': '1'})
        results = []
        for dsobj in self.dsobjects:
            logging.error(dir(dsobj))
            title = ''
            desc = ''
            comment = []
            preview = None
            object_id = dsobj.object_id
            if hasattr(dsobj, 'metadata'):
                if 'title' in dsobj.metadata:
                    title = dsobj.metadata['title']
                if 'description' in dsobj.metadata:
                    desc = dsobj.metadata['description']
                if 'comments' in dsobj.metadata:
                    try:
                        comment = json.loads(dsobj.metadata['comments'])
                        _logger.debug(comment)
                    except:
                        comment = []
                """
                if 'mime_type' in dsobj.metadata and \
                   dsobj.metadata['mime_type'][0:5] == 'image':
                    preview = get_pixbuf_from_file(
                        dsobj.file_path,
                        int(PREVIEW[self._orientation][2] * self._scale),
                        int(PREVIEW[self._orientation][3] * self._scale))
                elif 'preview' in dsobj.metadata:
                    preview = get_pixbuf_from_journal(dsobj, 300, 225)
                """
            else:
                logging.debug('dsobj has no metadata')
            results.append({'title': title, 'desc': desc, 'comment': comment,
                    'id': object_id})
        return json.dumps(results)

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
