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

import SimpleHTTPServer
import SocketServer
import os

os.chdir(os.path.join(os.path.dirname(__file__), 'web'))


def setup_server():
    PORT = 2810
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(('', PORT), Handler)

    print 'serving at port', PORT

    return httpd

if __name__ == "__main__":
    server = setup_server()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print "Shutting down server"
        server.shutdown()
