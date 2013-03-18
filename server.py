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
import cgi
import dbus

from gi.repository import Gio
from sugar3 import network
from sugar3.datastore import datastore

from warnings import filterwarnings, catch_warnings
with catch_warnings():
    if sys.py3kwarning:
        filterwarnings("ignore", ".*mimetools has been removed",
                       DeprecationWarning)
    import mimetools

# Maximum input we will accept when REQUEST_METHOD is POST
# 0 ==> unlimited input
maxlen = 0


def parse_multipart(fp, pdict):
    """Parse multipart input.
    Copied from cgi.py , but modified to get the filename
    Arguments:
    fp   : input file
    pdict: dictionary containing other parameters of content-type header
    filenamedict: dictionary containing filenames if available
    """
    boundary = ""
    if 'boundary' in pdict:
        boundary = pdict['boundary']
    if not cgi.valid_boundary(boundary):
        raise ValueError('Invalid boundary in multipart form: %r' % boundary)

    nextpart = "--" + boundary
    lastpart = "--" + boundary + "--"
    partdict = {}
    filenamesdict = {}
    terminator = ""

    while terminator != lastpart:
        bytes = -1
        data = None
        if terminator:
            # At start of next part.  Read headers first.
            headers = mimetools.Message(fp)
            clength = headers.getheader('content-length')
            if clength:
                try:
                    bytes = int(clength)
                except ValueError:
                    pass
            if bytes > 0:
                if maxlen and bytes > maxlen:
                    raise ValueError('Maximum content length exceeded')
                data = fp.read(bytes)
            else:
                data = ""
        # Read lines until end of part.
        lines = []
        while 1:
            line = fp.readline()
            if not line:
                terminator = lastpart  # End outer loop
                break
            if line[:2] == "--":
                terminator = line.strip()
                if terminator in (nextpart, lastpart):
                    break
            lines.append(line)
        # Done with part.
        if data is None:
            continue
        if bytes < 0:
            if lines:
                # Strip final line terminator
                line = lines[-1]
                if line[-2:] == "\r\n":
                    line = line[:-2]
                elif line[-1:] == "\n":
                    line = line[:-1]
                lines[-1] = line
                data = "".join(lines)
        line = headers['content-disposition']
        if not line:
            continue
        key, params = cgi.parse_header(line)
        if key != 'form-data':
            continue
        if 'name' in params:
            name = params['name']
        else:
            continue

        if name in partdict:
            partdict[name].append(data)
        else:
            partdict[name] = [data]

        if 'filename' in params:
            filename = params['filename']

        if name in filenamesdict:
            filenamesdict[name].append(filename)
        else:
            filenamesdict[name] = [filename]

    return partdict, filenamesdict


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

    def do_POST(self):
        if self.path == '/datastore/upload':
            ctype = self.headers.get('content-type')
            if not ctype:
                return None
            ctype, pdict = cgi.parse_header(ctype)
            file_fields, filenames = parse_multipart(self.rfile, pdict)

            i = 0
            preview_content = None
            metadata_content = None
            for file_name in filenames['journal_item']:
                if file_name == 'preview':
                    preview_content = file_fields['journal_item'][i]
                elif file_name == 'metadata':
                    metadata_content = file_fields['journal_item'][i]
                else:
                    file_content = file_fields['journal_item'][i]
                    # save to the journal
                    new_dsobject = datastore.create()
                    file_path = os.path.join(self.server.activity_root,
                            'instance', file_name)
                    f = open(file_path, 'w')
                    try:
                        f.write(file_content)
                    finally:
                        f.close()
                i = i + 1

            #Set the file_path in the datastore.
            new_dsobject.set_file_path(file_path)
            if metadata_content is not None:
                metadata = json.loads(metadata_content)
                for key in metadata.keys():
                    new_dsobject.metadata[key] = metadata[key]
            if preview_content is not None and preview_content != '':
                new_dsobject.metadata['preview'] = \
                        dbus.ByteArray(preview_content)

            # mark as favorite
            new_dsobject.metadata['keep'] = '1'

            datastore.write(new_dsobject)
            #redirect to index.html page
            self.send_response(301)
            self.send_header('Location', '/web/index.html')
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
                    mime_type, title, content = jm.get_object_by_id(object_id)
                    self.send_header_response(mime_type, title)
                    self.wfile.write(content)
                if self.path.startswith('/datastore/preview/id='):
                    object_id = self.path[self.path.find('=') + 1:]
                    preview = jm.get_preview_by_id(object_id)
                    self.send_header_response('image/png')
                    self.wfile.write(preview)

    def send_header_response(self, mime_type, file_name=None):
        self.send_response(200)
        self.send_header("Content-type", mime_type)
        if file_name is not None:
            self.send_header("Content-Disposition",
                    "inline; filename='%s'" % file_name)
        self.end_headers()


class JournalHTTPServer(network.GlibTCPServer):
    """HTTP Server for transferring document while collaborating."""

    def __init__(self, server_address, activity_path, activity_root):
        """Set up the GlibTCPServer with the JournalHTTPRequestHandler.
        """
        self.activity_path = activity_path
        self.activity_root = activity_root
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
        title = None
        if 'title' in dsobj.metadata:
            title = dsobj.metadata['title']

        f = open(dsobj.file_path, 'r')
        # TODO: read all the file in memory?
        content = f.read()
        f.close()
        return mime_type, title, content

    def get_preview_by_id(self, object_id):
        dsobj = datastore.get(object_id)
        preview = None
        if 'preview' in dsobj.metadata:
            preview = dsobj.metadata['preview']
        return preview

    def get_starred(self):
        self.dsobjects, self._nobjects = datastore.find({'keep': '1'})
        results = []
        for dsobj in self.dsobjects:
            title = ''
            desc = ''
            comment = []
            object_id = dsobj.object_id
            if hasattr(dsobj, 'metadata'):
                if 'title' in dsobj.metadata:
                    title = dsobj.metadata['title']
                if 'description' in dsobj.metadata:
                    desc = dsobj.metadata['description']
                if 'comments' in dsobj.metadata:
                    try:
                        comment = json.loads(dsobj.metadata['comments'])
                    except:
                        comment = []
            else:
                logging.debug('dsobj has no metadata')
            results.append({'title': title, 'desc': desc, 'comment': comment,
                    'id': object_id})
        return json.dumps(results)


def setup_server(activity_path, activity_root, port):
    server = JournalHTTPServer(("", port), activity_path, activity_root)
    return server


if __name__ == "__main__":
    activity_path = sys.argv[1]
    activity_root = sys.argv[2]
    port = int(sys.argv[3])
    server = setup_server(activity_path, activity_root, port)
    try:
        logging.debug("Before start server")
        server.serve_forever()
    except KeyboardInterrupt:
        print "Shutting down server"
        server.shutdown()
